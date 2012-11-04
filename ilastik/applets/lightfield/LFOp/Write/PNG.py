'''
Created on Jul 9, 2012

@author: fredo
'''

# TODO: this operator does not work yet with lfs that have multiple "rows"
# furthermore: I struggled with the builtin np funcs, as they seemed to produce weird results when using resize() or put()
#              row.resize(newShape,refcheck = False)
#              np.put(row,
#                     range(startIndex,endIndex),
#                     lf[i,j],
#                     mode = "raise")

from lazyflow.graph import Operator, InputSlot, OutputSlot
from scipy.misc import imsave
from LFOp.Util import shapeToSlice
from LFOp import NativeUtil
import numpy as np

class WritePNGOperator(Operator):
  """
  @author: Frederik Claus
  @summary: Writes the whole lf into one image file
  @param inFile: path of the image file
  @param inLf: input lf
  """
  inLf = InputSlot()
  inFile = InputSlot()
  outLf = OutputSlot()
  
  def execute(self, slot, roi, result):
    lf = self.inLf.value 
    shape = lf.shape
    ndim = lf.ndim
    hRes = shape[0]
    vRes = shape[1]
    yRes = shape[2]
    xRes = shape[3]
    
  #        row = np.ndarray(shape = (shape[3],shape[4]),dtype = lf.dtype)
    row = None
    rows = None
    
    if ndim == 5:
      resizeShape = (yRes,xRes,3)
    else:
      resizeShape = (yRes,xRes)
    
    for i in range(hRes):
      # put all images of one row into one MxN array
      for j in range(vRes):
        
        if row is None:
          row = lf[i,j].copy()
          
        else:
          oldShape = row.shape
          
          if ndim == 5:
            newShape = (yRes,oldShape[1] + xRes,3)
          else:
            newShape = (yRes,oldShape[1] + xRes)
          
            
          print "resizing to %s" % (str(newShape))
  
          # resize 
          newRow = np.zeros(shape = newShape,dtype = row.dtype)
          # copy old data
          NativeUtil.put(row,newRow)
          # append new image
          NativeUtil.append(lf[i,j],newRow,oldShape)
         
              
          row = newRow
  
          1+1
      # put all rows into one row
      if rows is None:
        rows = row.copy()
        
      else:
        oldShape = rows.shape
        
        if ndim == 5:
          newShape = (oldShape[0] + yRes,xRes,3)
        else:
          newShape = (oldShape[0] + yRes,xRes)
          
        rows.resize(newShape,refcheck = False)
        startIndex = oldShape[0] * oldShape[1]
        endIndex = newShape[0] * newShape[1]
        rows.put(range(startIndex,endIndex),
                 row.flat,
                 mode = "raise")
          
        
    path = self.inFile.value
    imsave(path,rows)
    result[shapeToSlice(self.outLf.meta.shape)] = lf
  
  def setupOutputs(self):
  #        sets metadata on outputs
    self.outLf.meta.shape = self.inLf.meta.shape
    self.outLf.meta.dtype = self.inLf.meta.dtype
  
  def propagateDirty(self, slot, roi):
    pass
    
def writePNG(op,path):
  png = WritePNGOperator()
  png.inFile.setValue(path)
  png.inLf.connect(op.outLf)
  png.outLf[:].allocate().wait()

if __name__ == "__main__":
    
  from LFOp.Read.Blender import connectBlender
  from LFOp import settings 
  write = WritePNGOperator()
  
  
  connectBlender(write,noSlice = True)
  write.inFile.setValue(settings.TEST_OUTPNG)
  
  from LFOp.View.Simple import viewLf
  viewLf(write)