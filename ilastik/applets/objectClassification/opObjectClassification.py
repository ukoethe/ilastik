import numpy
import h5py
import vigra
import vigra.analysis

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque
from lazyflow.rtype import Everything, SubRegion, List
from lazyflow.operators.ioOperators.opStreamingHdf5Reader import OpStreamingHdf5Reader
from lazyflow.operators.ioOperators.opInputDataReader import OpInputDataReader
from lazyflow.operators import OperatorWrapper, OpBlockedSparseLabelArray, OpValueCache
from lazyflow.request import Request, Pool
from functools import partial

from ilastik.applets.pixelClassification.opPixelClassification import OpShapeReader, OpMaxValue 

class OpObjectTrain(Operator):
    name = "TrainRandomForestObjects"
    description = "Train a random forest on multiple images"
    category = "Learning"

    inputSlots = [InputSlot("Images", level=1), InputSlot("Features", level=1, stype=Opaque, rtype=List ),InputSlot("Labels", level=1),\
                   InputSlot("fixClassifier", stype="bool"), InputSlot("nonzeroLabelBlocks", level=1)]
    outputSlots = [OutputSlot("Classifier")]

    def __init__(self, *args, **kwargs):
        super(OpObjectTrain, self).__init__(*args, **kwargs)
        #self.progressSignal = OrderedSignal()
        self._forest_count = 10
        # TODO: Make treecount configurable via an InputSlot
        self._tree_count = 10

    def setupOutputs(self):
        if self.inputs["fixClassifier"].value == False:
            self.outputs["Classifier"].meta.dtype = object
            self.outputs["Classifier"].meta.shape = (self._forest_count,)
            self.outputs["Classifier"].meta.axistags  = "classifier"
            
    #@traceLogged(logger, level=logging.INFO, msg="OpTrainRandomForestBlocked: Training Classifier")
    def execute(self, slot, subindex, roi, result):

        numImages = len(self.Features)

        key = roi.toSlice()
        featMatrix=[]
        labelsMatrix=[]
        imageMatrix = []
        self.objectIndices = set()
        
        for i,labels in enumerate(self.inputs["Labels"]):
            if labels.meta.shape is not None:
                #labels=labels[:].allocate().wait()
                blocks = self.inputs["nonzeroLabelBlocks"][i][0].allocate().wait()

                reqlistlabels = []
                reqlistfeat = []
                print "Sending requests for {} non-zero blocks (labels and data)".format( len(blocks[0])) 
                #traceLogger.debug("Sending requests for {} non-zero blocks (labels and data)".format( len(blocks[0])) )
                for b in blocks[0]:

                    request = labels[b].allocate()
                    featurekey = list(b)
                    featurekey[-1] = slice(None, None, None)
                    request2 = self.inputs["Images"][i][featurekey].allocate()

                    reqlistlabels.append(request)
                    reqlistfeat.append(request2)

                #traceLogger.debug("Requests prepared")
                print "requests prepared"

                numLabelBlocks = len(reqlistlabels)
                
                for ir, req in enumerate(reqlistlabels):
                    print "Waiting for a label block"
                    #traceLogger.debug("Waiting for a label block...")
                    labblock = req.wait()

                    #traceLogger.debug("Waiting for an image block...")
                    image = reqlistfeat[ir].wait()

                    indexes=numpy.nonzero(labblock[...,0].view(numpy.ndarray))
                    
                    self.objectIndices = self.objecIndices.union(set(image[indexes]))
                    
                    
                    imageValues=image[indexes]
                    labbla=labblock[indexes]

                    imageMatrix.append(imageValues)
                    labelsMatrix.append(labbla)


        if len(imageMatrix) == 0 or len(labelsMatrix) == 0:
            # If there was no actual data for the random forest to train with, we return None
            result[:] = None
        else:
            
            
            
            featMatrix=numpy.concatenate(featMatrix,axis=0)
            labelsMatrix=numpy.concatenate(labelsMatrix,axis=0)

            try:
                # train and store self._forest_count forests in parallel
                pool = Pool()

                for i in range(self._forest_count):
                    def train_and_store(number):
                        result[number] = vigra.learning.RandomForest(self._tree_count) 
                        result[number].learnRF(featMatrix.astype(numpy.float32),labelsMatrix.astype(numpy.uint32))
                    req = pool.request(partial(train_and_store, i))

                pool.wait()
                pool.clean()

            except:
#                logger.error( "ERROR: could not learn classifier" )
#                logger.error( "featMatrix shape={}, max={}, dtype={}".format(featMatrix.shape, featMatrix.max(), featMatrix.dtype) )
#                logger.error( "labelsMatrix shape={}, max={}, dtype={}".format(labelsMatrix.shape, labelsMatrix.max(), labelsMatrix.dtype ) )
                print "somethin gone wrong in training"
                raise
            #finally:
            #    self.progressSignal(100)
        
        return result

    def propagateDirty(self, slot, subindex, roi):
        if slot is not self.fixClassifier and self.inputs["fixClassifier"].value == False:
            self.outputs["Classifier"].setDirty((slice(0,1,None),))



class OpObjectClassification(Operator):
    
    name = "OpObjectClassification"
    category = "Top-level"
    
    #BinaryImage = InputSlot()
    InputImages = InputSlot(level = 1)
    ObjectFeatures = InputSlot( level = 1, stype=Opaque, rtype=List )
    
    #ConnCompImages = InputSlot(level = 1)
    LabelsAllowedFlags = InputSlot(stype='bool', level=1) # Specifies which images are permitted to be labeled 
    LabelInputs = InputSlot(optional = True, level=1) # Input for providing label data from an external source
    
    #FIXME/REMOVEME
    OutputPath = InputSlot()
    
    MaxLabelValue = OutputSlot()
    #FIXME: maybe this should be a list of clicks
    LabelImages = OutputSlot(level=1) # Labels from the user
    NonzeroLabelBlocks = OutputSlot(level=1) # A list if slices that contain non-zero label values
    
    #ConnCompImage = OutputSlot(level=1)
    
    def __init__(self, *args, **kwargs):
        super(OpObjectClassification, self).__init__(*args, **kwargs)
        #self.opConnComp = OperatorWrapper( OpInputDataReader, parent = self, graph=self.graph)
        #self.opConnComp.inputs["FilePath"].setValue("/home/akreshuk/data/3dcube_cc.h5/volume/data")
        #self.ConnCompImage.connect(self.opConnComp.Output)
        
        self.opInputShapeReader = OperatorWrapper( OpShapeReader, parent=self, graph=self.graph )
        self.opInputShapeReader.Input.connect( self.InputImages )
        self.opLabelArray = OperatorWrapper( OpBlockedSparseLabelArray, parent=self, graph=self.graph )
        self.opLabelArray.inputs["shape"].connect( self.opInputShapeReader.OutputShape )
        self.opMaxLabel = OpMaxValue(graph=self.graph)
        
        #self.opTrain = OperatorWrapper(OpObjectTrain, graph = self.graph)
        #self.opObjectTrain.inputs["Features"].connect(self.ObjectFeatures)
        
        
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