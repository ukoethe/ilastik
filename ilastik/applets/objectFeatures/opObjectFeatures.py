import numpy
import h5py
import vigra
import vigra.analysis

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque
from lazyflow.rtype import Everything, SubRegion, List
from lazyflow.operators.ioOperators.opStreamingHdf5Reader import OpStreamingHdf5Reader
from lazyflow.operators.ioOperators.opInputDataReader import OpInputDataReader

def OpObjectFeatures(Operator):
    
    name = "OpObjectFeatures"
    category = "Top-level"
    
    #BinaryImage = InputSlot()
    InputImage = InputSlot()
    
    LabeledImage = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super(OpObjectFeatures, self).__init__(*args, **kwargs)
        self.opConnComp = OpInputDataReader(parent = self)
        self.LabeledImage.connect(self.opConnComp.OutputImage)
        
    
    def setupOutputs(self):
        self.opConnComp.inputs["FilePath"].setValue("/home/akreshuk/data/test_image_cc.h5/volume/data")
        
    def propagateDirty(self, slot, subindex, roi):
        # Output slots are directly connected to internal operators
        pass 