'''
Created on Jul 9, 2012

@author: fredo
'''


from lazyflow.graph import Operator, InputSlot, OutputSlot
from LFLib.Blender import fromBlender,parseLogfile

import numpy as np
import vigra
import os
from LFOp import Util
import glob
from scipy.misc import imread
from numpy import meshgrid

class ReadBlenderOperator(Operator):
    
    inDir = InputSlot()
    inChannel = InputSlot()
    outLf = OutputSlot()
    
    def execute(self, slot, roi, result):
      path = self.inDir.value
      channel = self.inChannel.value
      lf = fromBlender(path,channel = channel)
      # no slicing supported, always insert the 'full' slice
      result[Util.shapeToSlice(self.outLf.meta.shape)] = lf.lf

    def setupOutputs(self):
      # all meta information must be present before execute, because execute() of piped operators are called in reverse order
      meta = getMeta(self.inDir.value,self.inChannel.value)
      for key in meta:
        self.outLf.meta[key] = meta[key]
#      self.outLf.meta["inChannel"] = self.inChannel.value
      # this defines the datatype of the data in the dataset 
      # it does not define the datatype of the array
      self.outLf.meta.dtype = np.uint8
      
    def propagateDirty(self, slot, roi):
        pass
    
   
def getMeta(renderPath,channel):
  """
  @author: Frederik Claus
  @summary: Returns all meta data of LF
  """
  params = parseLogfile(os.path.join(renderPath,"LF_logfile.txt"))
  vRes = params["steps"][0]*2+1;
  hRes = params["steps"][1]*2+1;
  imRes = getResolution(os.path.join(renderPath,"images"))
  yRes = imRes[0]
  xRes = imRes[1]
  params["channel"] = channel
  params["shape"] = (vRes,hRes,yRes,xRes,channel)
  params["xRes"] = xRes
  params["yRes"] = yRes
  params["hRes"] = hRes
  params["vRes"] = vRes
  if params["steps"][1] != 0:
    dH = params["space_range"][1]/float(params["steps"][1])
  else: 
    dH = 0
  if params["steps"][0] != 0:
    dV = params["space_range"][0]/float(params["steps"][0])
  else: 
    dV = 0
  params["dH"] = dH
  params["dV"] = dV
  params["focalLength"] = params["focal_length"]
  params["camDistance"] = params["cam_distance"]
  grid_h = np.arange(-params["steps"][1],params["steps"][1]+1,dtype=np.float32)
  grid_v = np.arange(-params["steps"][0],params["steps"][0]+1,dtype=np.float32)
  hSampling,vSampling = meshgrid(grid_h,grid_v)
  vSampling*=dV
  hSampling*=dH
  params["hSampling"] = hSampling
  params["vSampling"] = vSampling
  return params

def getResolution(path):
  files = getImages(path, "png")
  try:
    img = imread(files[0])[:,:]
    return (img.shape[0],img.shape[1])
  except:
    print "Could not read image"

def getImages(path,filetype):
  files = []
  for f in glob.glob(os.path.join(path,"*."+filetype)):
    files.append(f)
    
  files.sort()
  return files
      
def connectBlender(op, path = None, noSlice = False, slize = None):
  """
  @author: Frederik Claus
  @summary: connects ReadBlenderOperator to op
  @param op: operator to connect to
  @param path: path of the blender folder
  @param noSlice: if true read full lf, else read only the slice
  @param slice: if noSlice is False, apply this slice
  """
  from LFOp.settings import TEST_384x25_PATH
  from LFOp.Edit.Slicer import EditSlicerOperator
  
  blender = ReadBlenderOperator()
  slicer = EditSlicerOperator()
  
  if path is None:
    path = TEST_384x25_PATH
    
  blender.inDir.setValue(path)
  blender.inChannel.setValue(3)
  
  if noSlice:
    op.inLf.connect(blender.outLf)
  else:
    if slize is None:
      slize = (0,(4,8),None,None)
    op.inLf.connect(slicer.outLf)
    slicer.inSlice.setValue(slize)
    slicer.inLf.connect(blender.outLf)
 
  return op
    

if __name__ == "__main__":
  from LFOp.settings import TEST_384x25_PATH
  
  read = ReadBlenderOperator()
  read.inDir.setValue(TEST_384x25_PATH)
  read.inChannel.setValue(1)
  
#  # it does not really matter what you slice here
#  result = read.outLf[:].allocate().wait()
  
  from LFOp.View.Simple import viewLf
  viewLf(read)
  