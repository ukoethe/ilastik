import numpy as np
import numpy.ma as ma
import vigra
import scipy.misc as mi
import scipy.ndimage as nd
import h5py as h5
from sys import exit
import types

from LFLib.LightField import loadLF
from LFLib.ImageProcessing.ui import show
from LFLib.ImageProcessing.improc import colorRange
from helpers import *


def getLF(name):
  lf = loadLF(name)
  if lf.channels == 3:
    lf = 0.3*lf.lf[:,:,:,:,0]+0.59*lf.lf[:,:,:,:,1]+0.11*lf.lf[:,:,:,:,2]
  else:
    lf = lf.lf[:,:,:,:,0]
  return lf
  
  
  
def getSubspace(lf,v=None,h=None):
  if h is None and v is not None:
    return lf[v,:,:,:]
  if v is None and h is not None:
    return lf[:,h,:,:]
  if (v is None and h is None) or (v is not None and h is not None):
    print "Error in getSubspace!"
    exit()
    
    
    
def getEpi(lf,v=None,h=None,spatial=None):
  if v is None and h is not None and type(spatial) is types.IntType:
    return lf[:,h,:,spatial]
  elif h is None and v is not None and type(spatial) is types.IntType:
    return lf[v,:,spatial,:]
  else:
    print "Error in getEpi!"
    exit()
    
    
    
def subToLF(sub,empty_dim):
  if empty_dim == "v":
    outLF = np.zeros((1,sub.shape[0],sub.shape[1],sub.shape[2]),dtype=sub.dtype)
    outLF[0,:,:,:] = sub[:]
    return outLF
  elif empty_dim == "h":
    outLF = np.zeros((sub.shape[0],1,sub.shape[1],sub.shape[2]),dtype=sub.dtype)
    outLF[:,0,:,:] = sub[:]
    return outLF
  else:
    print "Error in subToLF!"
    exit()
    
    
    
def refocusLF(lf,shift=0):
  sy = lf.shape[0]/2
  sx = lf.shape[1]/2
  sy = range(-sy,sy+1) 
  sx = range(-sx,sx+1)
  
  if lf.shape[0]%2 == 0:
    sy.remove(0)
  if lf.shape[1]%2 == 0:
    sx.remove(0)
  
  outLF = np.copy(lf)
  for i,y in enumerate(sy):
    for j,x in enumerate(sx):
      shiftvec = [y*shift,x*shift]
      outLF[i,j,:,:] = nd.interpolation.shift(outLF[i,j,:,:],shiftvec)
  return outLF
  
  
  
def refocusEpi(epi,shift=0,order=3):
  sy = epi.shape[0]
  sx = epi.shape[1]
  y = range(-sy/2,sy/2+1) 
  
  print "sy",sy
  print "sx",sx
  print "y",y
  
  if sy%2 == 0:
    y.remove(0)
    
  
  outEpi = np.copy(epi)
  for i,_y in enumerate(y):
    shiftvec = _y*shift
    outEpi[i,:] = nd.interpolation.shift(outEpi[i,:],shiftvec)
  return outEpi
      
      
      
      
def showEpi(lf,v=None,h=None,spatial=None):
  if v is None and h is not None and type(spatial) is types.IntType:
    show([lf[:,h,:,spatial]],["h ="+str(h)+" x ="+str(spatial)])
  if h is None and v is not None and type(spatial) is types.IntType:
    show([lf[v,:,spatial,:]],["v ="+str(v)+" y ="+str(spatial)])
  if h is not None and v is not None and spatial is not None:
    if type(spatial) == types.IntType:
      show([lf[v,:,spatial,:],lf[:,h,:,spatial]],["v ="+str(v)+" y ="+str(spatial),"h ="+str(h)+" x ="+str(spatial)])
    elif type(spatial) == types.ListType:
      show([lf[v,:,spatial[0],:],lf[:,h,:,spatial[1]]],["v ="+str(v)+" y ="+str(spatial[0]),"h ="+str(h)+" x ="+str(spatial[1])])
    else:
      print "Error in showEpi!"
      exit()
      
      
      
      
def segmentate(lf):
  pass





#############################################################################################################
#############################################################################################################
#############################################################################################################



def loadSingleEpi(fname,rgb=True):
  epi = mi.imread(fname).astype(np.float32)
  if len(epi.shape)==2:
    tmp = np.zeros((epi.shape[0],epi.shape[1],1),dtype=np.float32)
    tmp[:,:,0] = epi[:,:]
    epi = tmp
  else:
    if epi.shape[2] == 4:
      epi = epi[:,:,0:3]
    if rgb == False:
      epi = 0.3*epi[:,:,0]+0.59*epi[:,:,1]+0.11*epi[:,:,2]
  return epi



def shiftEpi(epi,shift=0,order=3):
  sy = epi.shape[0]
  channels = epi.shape[2]
  y = range(-sy/2+1,sy/2+1) 
  
  oldRange = []
  for c in range(channels): 
    oldRange.append([np.amin(epi[:,:,c]),np.amax(epi[:,:,c])])
    
  if sy%2 == 0:
    print "remove 0!"
    y.remove(0)
    
    
  outEpi = np.zeros_like(epi)
  for channel in range(epi.shape[2]):
    for i,_y in enumerate(y):
      shiftvec = _y*shift
      outEpi[i,:,channel] = nd.interpolation.shift(epi[i,:,channel],shiftvec)
    outEpi[:,:,channel] = colorRange(outEpi[:,:,channel],oldRange[channel])
      
  
  return outEpi
  
  

def normColorSpace(im):
  return np.sqrt(im[:,:,0]**2+im[:,:,1]**2+im[:,:,2]**2)
  
  

def getStatisticSpaces(epi,mask,fromDisp,toDisp,steps):
  totalRange = np.abs(toDisp-fromDisp)
  stepSize = totalRange/steps
  sign = 1
  if fromDisp > toDisp:
    sign = -1
  
  meanSpace = np.zeros((steps,epi.shape[1],3),dtype=np.float32)
  stdSpace = np.zeros((steps,epi.shape[1],3),dtype=np.float32)

  shifts = []

  for step in range(steps+1):
    shift = fromDisp+step*sign*stepSize
    shifts.append(shift)
    epi_s = shiftEpi(epi,shift=shift,order=3)
    mask_s = shiftEpi(mask,shift=shift,order=3)
    for channel in range(epi.shape[2]):
      epi_s = ma.masked_array(data=epi_s,mask=mask_s)
      meanSpace[steps-1-step,:,channel] = np.mean(epi_s[:,:,channel],axis=0)
      stdSpace[steps-1-step,:,channel] = np.std(epi_s[:,:,channel],axis=0)
  
  stdSpace = normColorSpace(stdSpace)
  
  return meanSpace,stdSpace,np.array(shifts)
 
 
def updateMask(mask,labeled,shifts,shiftIndices):  
  sy = mask.shape[0]
  channels = mask.shape[2]
  y_range = range(-sy/2+1,sy/2+1); #print "update mask y range",y_range
  
  if sy%2 == 0:
    print "remove 0!"
    y_range.remove(0)
  
  for x in range(mask.shape[1]):
    if shiftIndices[x] != -1:
      shift = shifts[shiftIndices[x]]; #print "shift",shift
      for y,t in enumerate(y_range):
        try:
          mask[y,int(np.round(x+t*(shift-1.02066115702)))] = 1 
        except:
          pass
    
  return mask
  
  
def labelMinStdDevs(stdSpace,threshold,label=1):
  candidates = np.where(stdSpace<threshold)
  labelImg = np.zeros_like(stdSpace).astype(np.uint8)
  labelImg[candidates] = label
  
  return labelImg
  





   
  