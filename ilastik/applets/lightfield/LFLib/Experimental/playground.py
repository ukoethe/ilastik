import numpy as np
import scipy as sp
import scipy.ndimage as nd
import scipy.misc as mi
from LFLib.LFDepth.depthFromStructureTensor import *
from LFLib.ImageProcessing.ui import *
from LFLib.ImageProcessing.filter import *
from LFLib.Blender import *
from LFLib.LightField import *













##################################################################################################################
##################################################################################################################
##################################################################################################################

from scipy.ndimage import *

def structure_tensor_2D(im,inner,outer):
  sy=im.shape[0]
  sx=im.shape[1]
  
  if len(im.shape)>=3:
    print "convert to gray"
    im = 0.3*im[:,:,0]+0.59*im[:,:,1]+0.11*im[:,:,2]
    
  
  gauss = np.zeros_like(im).astype(np.float32)
  dy = np.zeros_like(im).astype(np.float32)
  dx = np.zeros_like(im).astype(np.float32)
  
  gaussian_filter(im, sigma=inner, order=0, output=gauss, mode='nearest')

  sobel(gauss,output=dy,mode="nearest",axis=0)
  sobel(gauss,output=dx,mode="nearest",axis=1)
  
  tensor = np.zeros((sy,sx,3),dtype=np.float32)
  
  gaussian_filter(dy[:]**2,sigma=outer, order=0, output=tensor[:,:,0], mode='nearest')
  gaussian_filter(dx[:]*dy[:],sigma=outer, order=0, output=tensor[:,:,1], mode='nearest')
  gaussian_filter(dx[:]**2,sigma=outer, order=0, output=tensor[:,:,2], mode='nearest')
  
  return tensor


def getDirections(tensor):
  dirs = 1/2.0*np.arctan2(2*tensor[:,:,1],tensor[:,:,2]-tensor[:,:,0])
  return np.tan(-dirs) 


def structure_tensor_4D(lf_array,inner,outer):
  sv=lf_array.shape[0]
  sh=lf_array.shape[1]
  sy=lf_array.shape[2]
  sx=lf_array.shape[3]
  
  gauss = np.zeros_like(lf_array).astype(np.float32)
  dy = np.zeros_like(lf_array).astype(np.float32)
  dx = np.zeros_like(lf_array).astype(np.float32)
  
  gaussian_filter(lf_array, sigma=inner, order=0, output=gauss, mode='nearest')

  sobel(gauss,output=dy,mode="nearest",axis=2)
  sobel(gauss,output=dx,mode="nearest",axis=3)
  
  tensor = np.zeros((sv,sh,sy,sx,3),dtype=np.float32)
  gaussian_filter(dx[:]**2,sigma=outer, order=0, output=tensor[:,:,:,:,0], mode='nearest')
  gaussian_filter(dx[:]*dy[:],sigma=outer, order=0, output=tensor[:,:,:,:,1], mode='nearest')
  gaussian_filter(dy[:]**2,sigma=outer, order=0, output=tensor[:,:,:,:,2], mode='nearest')
  
  return tensor




