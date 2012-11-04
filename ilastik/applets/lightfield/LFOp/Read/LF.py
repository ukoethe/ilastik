'''
Created on Aug 8, 2012

@author: fredo
'''


from lazyflow.graph import Operator, InputSlot, OutputSlot
from LFLib.LightField import loadLF
from numpy import copy
from h5py import File
from LFOp import Util

class ReadLFOperator(Operator):
    
    inFile = InputSlot()
    outLf = OutputSlot()
    
    def execute(self, slot, roi, result):
        lf = loadLF(self.inFile.value)
        Util.insertMeta(lf,self.outLf.meta)
#        loadLF only populates outLf
        result[Util.shapeToSlice(self.outLf.meta.shape)] = lf.lf
    
    def setupOutputs(self):
#        sets metadata on outputs
        f = File(self.inFile.value, 'r') 
        lf = copy(f["LF"])
        self.outLf.meta.shape = lf.shape
        self.outLf.meta.dtype = lf.dtype
        pass
    
    def propagateDirty(self, slot, roi):
        pass
    

if __name__ == "__main__":
  from LFOp.settings import TEST_LF
  from LFOp.View.Simple import viewLf
  
  read = ReadLFOperator()
  read.inFile.setValue(TEST_LF)
  
  # it does not really matter what you slice here
  viewLf(read)
