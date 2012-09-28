import numpy
import h5py
import vigra
import vigra.analysis

from lazyflow.graph import Operator, InputSlot, OutputSlot
from lazyflow.stype import Opaque
from lazyflow.rtype import Everything, SubRegion, List
from lazyflow.operators.ioOperators.opStreamingHdf5Reader import OpStreamingHdf5Reader
from lazyflow.operators.ioOperators.opInputDataReader import OpInputDataReader

class OpObjectFeatures(Operator):
    
    name = "OpObjectFeatures"
    category = "Top-level"
    
    #BinaryImage = InputSlot()
    InputImage = InputSlot()
    
    #FIXME/REMOVEME
    OutputPath = InputSlot()
    
    LabeledImage = OutputSlot()
    
    def __init__(self, *args, **kwargs):
        super(OpObjectFeatures, self).__init__(*args, **kwargs)
        self.opConnComp = OpInputDataReader(parent = self)
        self.LabeledImage.connect(self.opConnComp.Output)
        
    
    def setupOutputs(self):
        if self.OutputPath.ready():
            self.opConnComp.inputs["FilePath"].setValue(self.OutputPath.value)
        
    def propagateDirty(self, slot, subindex, roi):
        # Output slots are directly connected to internal operators
        pass 