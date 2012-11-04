'''
Created on Jul 25, 2012

@author: fredo
'''

from lazyflow.graph import Operator, InputSlot, OutputSlot
import matplotlib.cm as cm
import numpy as np
import pylab as plt
import types
from LFOp.Util import shapeToSlice,copyMeta
from decimal import Decimal

class ViewSimpleOperator(Operator):
    
  inLf = InputSlot()
  outLf = OutputSlot()
  cmap = "gray"
    
  def execute(self, slot, roi, result,):

    imgs = self.inLf.value   
    hRes = imgs.shape[0]
    vRes = imgs.shape[1]
    channel = imgs.shape[4]
    fig = plt.figure(figsize = (vRes,hRes))
      
#  lf stacks vertical not horizontal  
    height =  Decimal(1)/Decimal(hRes)
    width = Decimal(1)/Decimal(vRes)

    offset_x = 0
    for x in range(len(imgs)):
      offset_y = 0
      for y in range(len(imgs[x])):
        print "adding figure at [%f,%f,%f,%f]" % (offset_y,offset_x,width,height)
        fig.add_axes([offset_x,offset_y,width,height])
        im = imgs[x,y]
        channel = im.shape[2]
        if channel == 3:
          plt.imshow(im)
#          matplot only takes NxM for greyscale, not NxMx1
        elif channel == 1:
          plt.imshow(im.reshape((im.shape[0],im.shape[1])))
        offset_x += width
      offset_y += height
      
    plt.show()
    
    result[shapeToSlice(self.inLf.meta.shape)] = imgs
    
  def setupOutputs(self):
#        sets metadata on outputs
    copyMeta(self)
    self.outLf.meta.shape  = self.inLf.meta.shape
    self.outLf.meta.dtype = self.inLf.meta.dtype
    
  def propagateDirty(self, slot, roi):
    pass
    

def viewLf(op):
  view = ViewSimpleOperator()
  view.inLf.connect(op.outLf)
  view.outLf[:].allocate().wait()
  
if __name__ == "__main__":
  from LFOp.Read.Blender import connectBlender
  from LFOp.settings import TEST_384x25_PATH
  
  
  view = ViewSimpleOperator()
  
  connectBlender(view)
  
  view.outLf[:].allocate().wait()