'''
Created on Aug 8, 2012

@author: fredo
'''

from lazyflow.graph import Operator, InputSlot, OutputSlot
from LFLib.LightField import saveLF,LightField
from LFOp.Util import shapeToSlice, copyMeta
import copy

class WriteLFOperator(Operator):
    
    inLf = InputSlot()
    inFile = InputSlot()
    outLf = OutputSlot()
    
    def execute(self, slot, roi, result):
#      print self.inLf.meta.blah
      lf = fromOperator(self.inLf.value,self.inLf.meta)
      saveLF(lf,self.inFile.value)
      result[shapeToSlice(self.inLf.meta.shape)] = self.inLf.value
  
    def setupOutputs(self):
#        sets metadata on outputs
      copyMeta(self)
      self.outLf.meta.shape = self.inLf.meta.shape
      self.outLf.meta.dtype = self.inLf.meta.dtype
    
    def propagateDirty(self, slot, roi):
        pass
  
"""
@author: Frederik Claus
@summary: adds metadata to lf array for operator output
"""
def toOperator(lf):
  pass
    

def fromOperator(lf,meta):
  """
  @author: Frederik Claus
  @summary: Builds a LF from the raw lf data and the meta information
  @param lf: raw LF data as ndarray
  @param meta: dictionary holding meta information of LF
  """
  lfOut = LightField(channels = meta["channel"])
#  sets all the meta information
  for key in meta:
    setattr(lfOut,key,meta[key])
#  resolve different identifiers in meta dictionary and member variables
  lfOut.camDistance = meta["cam_distance"]
  lfOut.focalLength = meta["focal_length"]
#  append lf and outLf data
  lfOut.lf = lf
#  lfOut.outLf = copy(lf)
  return lfOut

if __name__ == "__main__":
    from LFOp.settings import TEST_384x25_PATH,TEST_OUTLF
    from LFOp.Read.Blender import ReadBlenderOperator
    
    blender = ReadBlenderOperator()
    write = WriteLFOperator()
    
    
    write.inLf.connect(blender.outLf)
    write.inFile.setValue(TEST_OUTLF)
    blender.inDir.setValue(TEST_384x25_PATH)
    blender.inChannel.setValue(3)
    
    
    write.outLf[:].allocate().wait()
    print "end"