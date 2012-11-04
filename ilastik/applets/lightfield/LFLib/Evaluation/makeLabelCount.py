import sys 
import numpy as np
from LFLib.Blender import disparityToDepth, depthToDisparity
from LFLib.LightField import saveLF,loadLF
from LFLib.Helpers import ensure_dir
from LFLib.ImageProcessing.ui import overlayShow,show
from LFLib.LFDepth.depth import calcDepth
from LFLib.ImageProcessing.filter import tv_regularizer

import matplotlib.pyplot as plt
from scipy.misc import imsave

from LFLib.settings import *



def plotGoodLabels(lf,allowedError,title,save,tvdenoised=None):
  
  if tvdenoised is not None:
    depth_inBU = disparityToDepth(tvdenoised,lf.dH,lf.camDistance,lf.focalLength,lf.xRes)
  else:
    depth_inBU = disparityToDepth(lf.depth,lf.dH,lf.camDistance,lf.focalLength,lf.xRes)
  
  amount,labelmap = countGoodLabels(depth_inBU,lf.gt,allowedError)
  
  #make good and bad label images
  overlayGood = np.zeros((lf.yRes,lf.xRes,3),dtype=np.uint8)
  overlayGood[:,:,1] = 255*labelmap[:]
  overlayBad = np.zeros((lf.yRes,lf.xRes,3),dtype=np.uint8)
  labelmap[:]*=-1
  labelmap[:]+=1
  overlayBad[:,:,0] = 255*labelmap[:]
  
  overlayShow(lf.lf[lf.vRes/2,lf.hRes/2,:,:,:],[overlayGood,overlayBad],allowedError,amount,title=title,alpha=0.5,saveTo=save)

  return amount



def countGoodLabels(depth_inBu,gt_inBu,delta):
  print "\ncountGoodLabels"
  diff = np.abs(depth_inBu[:]-gt_inBu[:])/gt_inBu[:]
  labelmap = np.zeros_like(depth_inBu)
  pixel = np.where(diff<=delta);
  labelmap[pixel] = 1
  
  amount = len(pixel[0])*100.0/(depth_inBu.shape[0]*depth_inBu.shape[1])
  
  return amount,labelmap







##########################################################################################
#
#                                        U S A G E 
#
##########################################################################################





def makeLabelCount(datakey,typekey=None,reskey=None,tv=None,allowedError=0.01,title="Label Error",saveloc="/tmp/lplot"):
  try:
    if typekey is not None and reskey is not None:
      fname = lfs[datakey][typekey][reskey]
    elif reskey is not None:
      fname = lfs[datakey][reskey]
    else:
      fname = lfs[datakey]
  except:
    print "Key Error..."
    sys.exit()
    
  save = saveloc
  
  lf = loadLF(fname)
  
  if lf.depth is None:
    print "\nNo depth data available, please enter scale parameter or abort and make a grid search:"
    c = raw_input('enter parameter: yes (y), no (n)?')
    if c.upper() == 'Y':
        inner = float(raw_input('enter innerscale:'))
        outer = float(raw_input('enter outerscale:'))
        calcDepth(lf,inner,outer)
    else:
      sys.exit()
      
  if tv is not None:
    from time import time
    t0 = time()
    print "\ntv denoising ...."
    depth_dn = tv_regularizer(lf.depth,tv["lambda"],tv["iter"],1)
    print "finished after",round(time()-t0,2),"s\n"
  
  plotGoodLabels(lf,allowedError,title,save)
  
  if tv is not None:
    save+="_tv1"
    plotGoodLabels(lf,allowedError,title,save)



def makeLabelCountFromLF(lf,tv=None,allowedError=0.01,title="Label Error",saveloc="/tmp/lplot"):
  save = saveloc
  
  if lf.depth is None:
    print "\nNo depth data available, please enter scale parameter or abort and make a grid search:"
    c = raw_input('enter parameter: yes (y), no (n)?')
    if c.upper() == 'Y':
        inner = float(raw_input('enter innerscale:'))
        outer = float(raw_input('enter outerscale:'))
        calcDepth(lf,inner,outer)
    else:
      sys.exit()
      
  if tv is not None:
    from time import time
    t0 = time()
    print "\ntv denoising ...."
    lf.depth = tv_regularizer(lf.depth,tv["lambda"],tv["iter"],1)
    print "finished after",round(time()-t0,2),"s\n"
  
  plotGoodLabels(lf,allowedError,title,save)
  
  if tv is not None:
    save+="_tv1"
    plotGoodLabels(lf,allowedError,title,save)
  