import numpy as np
import scipy.ndimage as nd
import libimproc as fast


def colormap(intensities,cmap):
  return fast._colormap(intensities,cmap)
  


def colorRange(arr,newRange=[0,255]):
  """
   @brief: adjust the value range of a ndarray to the newRange
   @param arr: <ndarray> input array
   @param newRange: <int list> new color range
   @return: <ndarray>
   """
  amin = np.amin(arr)
  amax = np.amax(arr)
  if amin == amax:
    return arr
  else:
    oldRange = [amin,amax]
    oldDiff = oldRange[1] - oldRange[0]
    newDiff = newRange[1] - newRange[0]
    out = (arr - oldRange[0]) / oldDiff * newDiff + newRange[0]
    return out
  

def rgbLF2hsvLF(lf,lf_out):
  from time import time
  t0 = time()
  fast._rgbLF2hsvLF(lf.astype(np.float32),lf_out)
  print "duration:",time()-t0,"s"
  
  
def hsvLF2rgbLF(lf,lf_out):
  from time import time
  t0 = time()
  fast._hsvLF2rgbLF(lf.astype(np.float32),lf_out)
  print "duration:",time()-t0,"s"
  