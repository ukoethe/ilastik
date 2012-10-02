import numpy
import h5py
import vigra
import vigra.analysis

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque
from lazyflow.rtype import Everything, SubRegion, List
from lazyflow.operators.ioOperators.opStreamingHdf5Reader import OpStreamingHdf5Reader
from lazyflow.operators.ioOperators.opInputDataReader import OpInputDataReader
from lazyflow.operators import OperatorWrapper, OpBlockedSparseLabelArray
from ilastik.applets.pixelClassification.opPixelClassification import OpShapeReader, OpMaxValue 

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
        
        print "label inputs len:", len(self.LabelInputs)
        print "label images len:", len(self.LabelImages)
        print "label blocks len:", len(self.NonzeroLabelBlocks)
        print "labels allowed flag:",len(self.LabelsAllowedFlags), "opt: ", self.LabelsAllowedFlags._optional
    
        #print "AAAAAAAAAAAAAAAa label array ready?", self.LabelImages.ready()
        
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