import numpy
import h5py
import vigra
import vigra.analysis
import copy

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque
from lazyflow.rtype import Everything, SubRegion, List
from lazyflow.operators.ioOperators.opStreamingHdf5Reader import OpStreamingHdf5Reader
from lazyflow.operators.ioOperators.opInputDataReader import OpInputDataReader
from lazyflow.operators import OperatorWrapper, OpBlockedSparseLabelArray, OpValueCache, \
OpMultiArraySlicer2, OpSlicedBlockedArrayCache, OpPrecomputedInput
from lazyflow.request import Request, Pool
from functools import partial

from ilastik.applets.pixelClassification.opPixelClassification import OpShapeReader, OpMaxValue 

class OpObjectTrain(Operator):
    name = "TrainRandomForestObjects"
    description = "Train a random forest on multiple images"
    category = "Learning"

    Features = InputSlot(level=2, stype=Opaque, rtype=List) # it's level 2, because for each dataset it's
                                                            # a list on time steps
    Labels = InputSlot(level=1, rtype=List) # a list of object labels, non-labeled objects have zero at their index
    FixClassifier = InputSlot(stype="bool")
    
    Classifier = OutputSlot()

    def __init__(self, *args, **kwargs):
        super(OpObjectTrain, self).__init__(*args, **kwargs)
        #self.progressSignal = OrderedSignal()
        self._forest_count = 10
        # TODO: Make treecount configurable via an InputSlot
        self._tree_count = 10

    def setupOutputs(self):
        if self.inputs["FixClassifier"].value == False:
            self.outputs["Classifier"].meta.dtype = object
            self.outputs["Classifier"].meta.shape = (self._forest_count,)
            self.outputs["Classifier"].meta.axistags  = None
            
    #@traceLogged(logger, level=logging.INFO, msg="OpTrainRandomForestBlocked: Training Classifier")
    def execute(self, slot, subindex, roi, result):

        numImages = len(self.Features)

        labels = self.inputs["Labels"].allocate().wait()
        print "I'm the execute function of the new training operator!"
        print "here are my labels:"
        print labels

    def propagateDirty(self, slot, subindex, roi):
        if slot is not self.FixClassifier and self.inputs["FixClassifier"].value == False:
            self.outputs["Classifier"].setDirty((slice(0,1,None),))


class OpObjectsPredict(Operator):
    name = "OpObjectsPredict"
    inputSlots = [InputSlot("Image"),InputSlot("Classifier"),InputSlot("LabelsCount",stype='integer')]
    outputSlots = [OutputSlot("PMaps")]
    
    inputSlots = [InputSlot("Image"),InputSlot("Classifier"),InputSlot("LabelsCount",stype='integer')]
    outputSlots = [OutputSlot("PMaps")]

    def setupOutputs(self):
        #FIXME: this will be a list of relabel tables
        nlabels=self.inputs["LabelsCount"].value
        self.PMaps.meta.dtype = numpy.float32
        self.PMaps.meta.axistags = copy.copy(self.Image.meta.axistags)
        self.PMaps.meta.shape = self.Image.meta.shape[:-1]+(nlabels,) # FIXME: This assumes that channel is the last axis
        self.PMaps.meta.drange = (0.0, 1.0)


    def execute(self, slot, subindex, roi, result):
        #randshape = result.shape
        result = numpy.random.random_sample(result.shape)
        return result
    
    def propagateDirty(self, slot, subindex, roi):
        self.outputs["PMaps"].setDirty(slice(None,None,None))
    

class OpObjectClassification(Operator):
    
    name = "OpObjectClassification"
    category = "Top-level"
    
    InputImages = InputSlot(level = 1)
    ObjectFeatures = InputSlot( level = 1, stype=Opaque, rtype=List )
    
    LabelsAllowedFlags = InputSlot(stype='bool', level=1) # Specifies which images are permitted to be labeled 
    LabelInputs = InputSlot(optional = True, level=1) # Input for providing label data from an external source
    
    FreezePredictions = InputSlot(stype='bool')

    PredictionsFromDisk = InputSlot(optional=True, level=1)
    
    
    MaxLabelValue = OutputSlot()
    #FIXME: maybe this should be a list of clicks
    LabelImages = OutputSlot(level=1) # Labels from the user
    NonzeroLabelBlocks = OutputSlot(level=1) # A list if slices that contain non-zero label values
    PredictionProbabilities = OutputSlot(level=1) # Classification predictions

    PredictionProbabilityChannels = OutputSlot(level=2) # Classification predictions, enumerated by channel
    
    def __init__(self, *args, **kwargs):
        super(OpObjectClassification, self).__init__(*args, **kwargs)
        
        self.opInputShapeReader = OperatorWrapper( OpShapeReader, parent=self, graph=self.graph )
        self.opInputShapeReader.Input.connect( self.InputImages )
        self.opLabelArray = OperatorWrapper( OpBlockedSparseLabelArray, parent=self, graph=self.graph )
        self.opLabelArray.inputs["shape"].connect( self.opInputShapeReader.OutputShape )
        self.opMaxLabel = OpMaxValue(graph=self.graph)
        
        self.opTrain = OpObjectTrain(graph = self.graph)
        self.predict = OperatorWrapper( OpObjectsPredict, parent=self, graph=self.graph )
        self.prediction_cache = OperatorWrapper( OpSlicedBlockedArrayCache, parent=self, graph=self.graph )
        assert len(self.prediction_cache.Input) == 0
        self.prediction_cache_gui = OperatorWrapper( OpSlicedBlockedArrayCache, parent=self, graph=self.graph )
        assert len(self.prediction_cache_gui.Input) == 0
        self.precomputed_predictions = OperatorWrapper( OpPrecomputedInput, parent=self, graph=self.graph )
        self.precomputed_predictions_gui = OperatorWrapper( OpPrecomputedInput, parent=self, graph=self.graph )

        
        # Set up other label cache inputs
        self.LabelInputs.connect( self.InputImages )
        self.opLabelArray.inputs["Input"].connect( self.LabelInputs )
        self.opLabelArray.inputs["eraser"].setValue(100)
                
        # Initialize the delete input to -1, which means "no label".
        # Now changing this input to a positive value will cause label deletions.
        # (The deleteLabel input is monitored for changes.)
        self.opLabelArray.inputs["deleteLabel"].setValue(-1)
        
        # Find the highest label in all the label images
        self.opMaxLabel.Inputs.connect( self.opLabelArray.outputs['maxLabel'] )
        
        
        self.opTrain.inputs["Features"].connect(self.ObjectFeatures)
        self.opTrain.inputs["Images"].connect(self.InputImages)
        self.opTrain.inputs['Labels'].connect(self.opLabelArray.outputs["Output"])
        self.opTrain.inputs["nonzeroLabelBlocks"].connect(self.opLabelArray.outputs["nonzeroBlocks"])
        self.opTrain.inputs['fixClassifier'].setValue(False)
        
        self.predict = OperatorWrapper( OpObjectsPredict, graph=self.graph)
        
        # The classifier is cached here to allow serializers to force in a pre-calculated classifier...
        self.classifier_cache = OpValueCache( graph=self.graph )
        self.classifier_cache.inputs["Input"].connect(self.opTrain.outputs['Classifier'])

        ##
        # 
        ##
        self.predict.inputs['Classifier'].connect(self.classifier_cache.outputs['Output']) 
        self.predict.inputs['Image'].connect(self.InputImages)
        self.predict.inputs['LabelsCount'].connect(self.opMaxLabel.Output)
        
        # prediction cache for downstream operators (if they want it)
        self.prediction_cache.name = "PredictionCache"
        self.prediction_cache.inputs["fixAtCurrent"].setValue(False)
        self.prediction_cache.inputs["Input"].connect( self.predict.PMaps )

        # The serializer uses these operators to provide prediction data directly from the project file
        # if the predictions haven't become dirty since the project file was opened.
        self.precomputed_predictions.SlowInput.connect( self.prediction_cache.Output )
        self.precomputed_predictions.PrecomputedInput.connect( self.PredictionsFromDisk )

        # Prediction cache for the GUI
        self.prediction_cache_gui.name = "PredictionCache"
        self.prediction_cache_gui.inputs["fixAtCurrent"].connect( self.FreezePredictions )
        self.prediction_cache_gui.inputs["Input"].connect( self.predict.PMaps )

        self.precomputed_predictions_gui.SlowInput.connect( self.prediction_cache_gui.Output )
        self.precomputed_predictions_gui.PrecomputedInput.connect( self.PredictionsFromDisk )

        
        
        # Also provide each prediction channel as a separate layer (for the GUI)
        self.opPredictionSlicer = OperatorWrapper( OpMultiArraySlicer2, parent=self, graph=self.graph )
        self.opPredictionSlicer.Input.connect( self.precomputed_predictions_gui.Output )
        self.opPredictionSlicer.AxisFlag.setValue('c')
        self.PredictionProbabilityChannels.connect( self.opPredictionSlicer.Slices )
        self.PredictionProbabilities.connect(self.predict.outputs["PMaps"])
        
        
        #Connect the outputs
        self.LabelImages.connect(self.opLabelArray.Output)
        self.MaxLabelValue.connect( self.opMaxLabel.Output )
        self.NonzeroLabelBlocks.connect(self.opLabelArray.nonzeroBlocks)
        
        def inputResizeHandler( slot, oldsize, newsize ):
            if ( newsize == 0 ):
                self.LabelImages.resize(0)
                self.NonzeroLabelBlocks.resize(0)
                self.PredictionProbabilities.resize(0)
                self.CachedPredictionProbabilities.resize(0)
        self.InputImages.notifyResized( inputResizeHandler )
        
        
        def handleNewInputImage( multislot, index, *args ):
            def handleInputReady(slot):
                self.setupCaches( multislot.index(slot) )
            multislot[index].notifyReady(handleInputReady)
                
        self.InputImages.notifyInserted( handleNewInputImage )
    
    
    def setupCaches(self, imageIndex):
        #Setup the label input to correct dimensions
        print "calling setup caches"
        numImages = len(self.InputImages)
        inputSlot = self.InputImages[imageIndex]
        #self.LabelImages.resize(numImages)
        self.LabelInputs.resize(numImages)

        # Special case: We have to set up the shape of our label *input* according to our image input shape
        shapeList = list(self.InputImages[imageIndex].meta.shape)
        try:
            channelIndex = self.InputImages[imageIndex].meta.axistags.index('c')
            shapeList[channelIndex] = 1
        except:
            pass
        self.LabelInputs[imageIndex].meta.shape = tuple(shapeList)
        self.LabelInputs[imageIndex].meta.axistags = inputSlot.meta.axistags
        
        # Set the blockshapes for each input image separately, depending on which axistags it has.
        axisOrder = [ tag.key for tag in inputSlot.meta.axistags ]
        
        ## Label Array blocks
        blockDims = { 't' : 1, 'x' : 64, 'y' : 64, 'z' : 64, 'c' : 1 }
        blockShape = tuple( blockDims[k] for k in axisOrder )
        self.opLabelArray.blockShape.setValue( blockShape )
                
    def setupOutputs(self):
        pass
    '''
        if self.OutputPath.ready():
            self.opConnComp.inputs["FilePath"].setValue(self.OutputPath.value)
            print "path set"
            print "output ready?", self.ConnCompImage.ready()
    '''
    
    
    def setInSlot(self, slot, subindex, roi, value):
        # Nothing to do here: All inputs that support __setitem__
        #   are directly connected to internal operators.
        pass

    def propagateDirty(self, slot, subindex, roi):
        # Output slots are directly connected to internal operators
        pass 