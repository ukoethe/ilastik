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
    
    LabelInputs = InputSlot(stype= Opaque, optional = True, level=1) # Input for providing label data from an external source
                                                                    # Labels come in the form of a list, as long as the number
                                                                    # of objects (see also relabeling property of the 
                                                                    # RelabelingLazyflowSourceSink in volumina
    
    FreezePredictions = InputSlot(stype='bool')

    #MaxObjectNumber = InputSlot(level=1, stype = Opaque)

    MaxLabelValue = OutputSlot()
    
    LabelOutputs = OutputSlot(level=1) # Labels from the user. We just give the connected components overlay again
    
    #FIXME: these are temporary, not needed for functionality, but for the labeling gui inteface
    Eraser = OutputSlot()
    DeleteLabel = OutputSlot()
    
    #FIXME: we'll need that when we are really predicting
    #PredictionProbabilities = OutputSlot(level=1) # Classification predictions

    #PredictionProbabilityChannels = OutputSlot(level=2) # Classification predictions, enumerated by channel
    
    def __init__(self, *args, **kwargs):
        super(OpObjectClassification, self).__init__(*args, **kwargs)
        
        self.opInputShapeReader = OperatorWrapper( OpShapeReader, parent=self, graph=self.graph )
        self.opInputShapeReader.Input.connect( self.InputImages )
        
        #self.opMaxLabel = OpMaxListValue(graph=self.graph)
        
        # Set up other label cache inputs
                
        # Initialize the delete input to -1, which means "no label".
        # Now changing this input to a positive value will cause label deletions.
        # (The deleteLabel input is monitored for changes.)
        #self.opLabelArray.inputs["deleteLabel"].setValue(-1)
        
        # Find the highest label in all the label images
        #self.opMaxLabel.Inputs.connect( self.opLabelArray.outputs['maxLabel'] )
    
        #self.opMaxLabel.Inputs.connect(self.LabelInputs)
        
        self.opTrain = OpObjectTrain(graph = self.graph)
        self.opTrain.inputs["Features"].connect(self.ObjectFeatures)
        self.opTrain.inputs['Labels'].connect(self.LabelInputs)
        self.opTrain.inputs['FixClassifier'].setValue(False)
        
        #Connect the outputs
        self.Eraser.setValue(100)
        self.DeleteLabel.setValue(-1)
        #self.MaxObjectNumber.setValue(19)
        self.LabelOutputs.connect( self.InputImages )
        #self.MaxLabelValue.connect( self.opMaxLabel.Output )
        self.MaxLabelValue.setValue(2)
        
        
        def handleNewInputImage( multislot, index, *args ):
            def handleInputReady(slot):
                self.setupCaches( multislot.index(slot) )
                '''
                print "meta info of operator slots:"
                print self.LabelInputs.meta.axistags
                print self.LabelOutputs.meta.axistags
                print self.LabelsAllowedFlags.meta.axistags
                print self.MaxObjectNumber.meta.axistags
                print self.InputImages.meta.axistags
                print self.ObjectFeatures.meta.axistags
                #self.LabelInputs.value.append([])
                '''
            multislot[index].notifyReady(handleInputReady)
                
        self.InputImages.notifyInserted( handleNewInputImage )
    
    
    def setupCaches(self, imageIndex):
        #Setup the label input to correct dimensions
        print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! calling setup caches"
        
        numImages = len(self.InputImages)
        
        self.LabelInputs.resize(numImages)

        self.LabelInputs[imageIndex].meta.shape = (1,)
        self.LabelInputs[imageIndex].meta.dtype = object
        self.LabelInputs[imageIndex].meta.axistags = None
        '''
        if self.MaxObjectNumber[imageIndex].ready():
            #FIXME: we set it to a list of arrays, because otherwise value only returns the first element
            self.LabelInputs[imageIndex].setValue([numpy.zeros((self.MaxObjectNumber[imageIndex].value+1))])
            print "set up label inputs", self.MaxObjectNumber[imageIndex].value, self.LabelInputs[imageIndex].value
        else:
            self.LabelInputs[imageIndex].setValue([])
        '''
        self.LabelInputs[imageIndex].setValue([numpy.zeros((20,))])
                
    def setupOutputs(self):
        pass
        '''
        if self.Features.ready():
            feats = self.Features[0]
            nobjects = feats[feats.activeNames()[0]].shape[0]
            self.maxObjectNumber.setValue(nobjects)
        '''
    
    def setInSlot(self, slot, subindex, roi, value):
        # Nothing to do here: All inputs that support __setitem__
        #   are directly connected to internal operators.
        pass

    def propagateDirty(self, slot, subindex, roi):
        # Output slots are directly connected to internal operators
        pass 
    
class OpMaxListValue(Operator):
    #For each image, the input is a relabeling vector
    Inputs = InputSlot(level=1) # A list of lists of values
    Output = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super(OpMaxListValue, self).__init__(*args, **kwargs)
        self.Output.meta.shape = (1,)
        self.Output.meta.dtype = object
        self._output = 0
        
    def setupOutputs(self):
        self.updateOutput()
        self.Output.setValue(self._output)

    def execute(self, slot, subindex, roi, result):
        result[0] = self._output
        return result

    def propagateDirty(self, inputSlot, subindex, roi):
        self.updateOutput()
        self.Output.setValue(self._output)

    def updateOutput(self):
        # Return the max value of all our inputs
        maxValue = None
        for i, inputSubSlot in enumerate(self.Inputs):
            # Only use inputs that are actually configured
            if inputSubSlot.ready():
                if len(inputSubSlot.value)>0:
                    curMax = numpy.max(inputSubSlot.value)
                    if maxValue is None:
                        maxValue = curMax
                    else:
                        maxValue = max(maxValue, curMax)
        
        if maxValue is None:
            self._output = 0
        else:
            self._output = maxValue


