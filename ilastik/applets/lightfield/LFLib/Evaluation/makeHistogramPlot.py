import sys
import numpy as np
from LFLib.Blender import disparityToDepth, depthToDisparity
from LFLib.LightField import saveLF,loadLF
from LFLib.LFDepth.depth import calcDepth
from LFLib.ImageProcessing.filter import tv_regularizer
from LFLib.ImageProcessing.ui import show
from scipy.misc import imsave

import matplotlib.pyplot as plt

from LFLib.settings import *
from time import time

def plot3LFs(lf_clean,lf_noisy,tv,save,bars=False):
  
  from time import time
  t0 = time()
  print "\ntv denoising ...."
  depth_dn = tv_regularizer(lf_clean.depth,tv["lambda"],tv["iter"],1)
  print "finished after",round(time()-t0,2),"s\n"
  
  fname = save+"_denoised.png"
  print "save denoised depth at:",fname
  imsave(fname,depth_dn)
  fname = save+"_clean.png"
  print "save clean depth at:",fname
  imsave(fname,lf_clean.depth)
  fname = save+"_noisy.png"
  print "save noisy depth at:",fname
  imsave(fname,lf_noisy.depth)
  
  X,err_clean,err_noisy,err_tv = eval3LFs(lf_clean,lf_noisy,depth_dn)
  
  if bars:
    p1 = plt.bar(X, err_noisy[:]*100,   width=0.1, color='r')
    p2 = plt.bar(X, err_clean[:]*100, width=0.1, color='y')
    p3 = plt.bar(X, err_tv[:]*100, width=0.1, color='g')
  else:
    l1 = plt.plot(X,err_noisy*100,'rs')
    l2 = plt.plot(X,err_clean*100,'yo')
    l3 = plt.plot(X,err_tv*100,'gp')
  
  plt.grid()
  
  plt.ylabel('mean deviation from gt in %')
  plt.xlabel('disparity')
  
  if bars:
    plt.legend( (p1[0], p2[0], p3[0]), ('noise', 'clean', 'tv L1 denoised') )
  else:
    plt.legend( (l1, l2, l3), ('noise', 'clean', 'tv L1 denoised') )
  
  
  if save is not None:
    if save.find(".svg") == -1:
      save+=".svg"
    plt.savefig(save)
    
  #plt.show()
  
  
  
def plot(lf,tv,save):
  
  
  t0 = time()
  print "\ntv denoising ...."
  depth_dn = tv_regularizer(lf.depth,tv["lambda"],tv["iter"],1)
  print "finished after",round(time()-t0,2),"s\n"
  
  
  
  X,err,err_tv = eval(lf,depth_dn)

  p1 = plt.bar(X, err,   width=0.1, color='r')
  p2 = plt.bar(X, err_tv, width=0.1, color='g')
  
  plt.ylabel('mean disparity error')
  plt.xlabel('disparity')
  plt.legend( (p1[0], p2[0]), ('lf', 'tv L1 denoised') )
  
  
  if save is not None:
    if save.find(".svg") == -1:
      save+=".svg"
    plt.savefig(save)
    
  plt.show()
  
  
  
  

def eval3LFs(lf_clean,lf_noisy,depth_dn):
  
  t0 = time()
  print "\neval3LFs ...",

  gt_inDisp = depthToDisparity(lf_clean.gt,lf_clean.dH,lf_clean.camDistance,lf_clean.focalLength,lf_clean.xRes)
  
  if False:
    mse = np.abs(np.abs(gt_inDisp[:])-np.abs(lf_clean.depth[:]))
    mse_noisy = np.abs(np.abs(gt_inDisp[:])-np.abs(lf_noisy.depth[:]))
    mse_tv = np.abs(np.abs(gt_inDisp[:])-np.abs(depth_dn[:]))
  if True:
    d_clean_inBE = disparityToDepth(lf_clean.depth,lf_clean.dH,lf_clean.camDistance,lf_clean.focalLength,lf_clean.xRes)
    d_noisy_inBE = disparityToDepth(lf_noisy.depth,lf_noisy.dH,lf_noisy.camDistance,lf_noisy.focalLength,lf_clean.xRes)
    d_dn_inBE = disparityToDepth(depth_dn,lf_clean.dH,lf_clean.camDistance,lf_clean.focalLength,lf_clean.xRes)
        
    mse = np.abs(d_clean_inBE[:]-lf_clean.gt[:])/lf_clean.gt[:]
    mse_noisy = np.abs(d_noisy_inBE[:]-lf_clean.gt[:])/lf_clean.gt[:]
    mse_tv = np.abs(d_dn_inBE[:]-lf_clean.gt[:])/lf_clean.gt[:]
  
  
  leftLimit = int(np.floor(np.amin(gt_inDisp)))
  rightLimit = int(np.ceil(np.amax(gt_inDisp)))
  distance = 0.1
  
  x = gt_inDisp.flatten()
  y = mse.flatten()
  y_noisy = mse_noisy.flatten()
  y_tv = mse_tv.flatten()
  
  
  X = np.arange(leftLimit,rightLimit+distance,distance)
  X[X.shape[0]/2] = 0
  numOfBins = X.shape[0]
  
  
  Y = np.zeros(numOfBins,dtype=np.float32)
  Y_noisy = np.zeros(numOfBins,dtype=np.float32)
  Y_tv = np.zeros(numOfBins,dtype=np.float32)
  
  for n in range(numOfBins): 
    print "\rcalc bin",n,"of",numOfBins,
    sign = 1
    if X[n]<0:
      sign = -1
      
    if n!=0 and n!=numOfBins-1:
      left = X[n]+sign*distance/2.0
      right = X[n]-sign*distance/2.0
    elif n==0:
      left = -10000
      right = leftLimit+distance/2.0
    elif n==numOfBins-1:
      right = 10000
      left = rightLimit-distance/2.0
      
    vals = []
    vals_noisy = []
    vals_tv = []
    for i in xrange(x.shape[0]):
      dispval = x[i] 
      
      if sign < 0:
        if dispval > left and dispval <= right:
          vals.append(y[i])
          vals_noisy.append(y_noisy[i])
          vals_tv.append(y_tv[i])
      if sign > 0:
        if dispval < left and dispval >= right:
          vals.append(y[i])
          vals_noisy.append(y_noisy[i])
          vals_tv.append(y_tv[i])
          
    if len(vals)!=0:
      Y[n] = np.mean(vals)
    if len(vals_noisy)!=0:
      Y_noisy[n] = np.mean(vals_noisy)
    if len(vals_tv)!=0:
      Y_tv[n] = np.mean(vals_tv)
    
  
  print "finished in",round(time()-t0,2),"s"
  return X,Y,Y_noisy,Y_tv




def eval(lf,depth_dn):
  
  gt_inDisp = depthToDisparity(lf.gt,lf.dH,lf.camDistance,lf.focalLength,lf.xRes)
  mse = np.abs(np.abs(gt_inDisp[:])-np.abs(lf.depth[:]))
  mse_tv = np.abs(np.abs(gt_inDisp[:])-np.abs(depth_dn[:]))

  leftLimit = int(np.floor(np.amin(gt_inDisp)))
  rightLimit = int(np.ceil(np.amax(gt_inDisp)))
  distance = 0.1
  
  x = gt_inDisp.flatten()
  y = mse.flatten()
  y_tv = mse_tv.flatten()
  
  
  X = np.arange(leftLimit,rightLimit+distance,distance)
  X[X.shape[0]/2] = 0
  numOfBins = X.shape[0]
  
  
  Y = np.zeros(numOfBins,dtype=np.float32)
  Y_tv = np.zeros(numOfBins,dtype=np.float32)
  
  for n in range(numOfBins): 
    print "calc bin",n,"of",numOfBins
    sign = 1
    if X[n]<0:
      sign = -1
      
    if n!=0 and n!=numOfBins-1:
      left = X[n]+sign*distance/2.0
      right = X[n]-sign*distance/2.0
    elif n==0:
      left = -10000
      right = leftLimit+distance/2.0
    elif n==numOfBins-1:
      right = 10000
      left = rightLimit-distance/2.0
      
    vals = []
    vals_tv = []
    for i in xrange(x.shape[0]):
      dispval = x[i] 
      
      if sign < 0:
        if dispval > left and dispval <= right:
          vals.append(y[i])
          vals_tv.append(y_tv[i])
      if sign > 0:
        if dispval < left and dispval >= right:
          vals.append(y[i])
          vals_tv.append(y_tv[i])
          
    if len(vals)!=0:
      Y[n] = np.mean(vals)
    if len(vals_tv)!=0:
      Y_tv[n] = np.mean(vals_tv)
    
  
  return X,Y,Y_tv






##########################################################################################
#
#                                        U S A G E 
#
##########################################################################################





def makeHistogramPlot(datakey,typekey=None,reskey=None,lamda=0.5,iter=200,saveloc="/tmp/hplot"):
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
  
  tv = {"lambda":lamda,"iter":iter}

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
  
  plot(lf,tv,save)
  
  

def makeCompareHistogramPlot(datakey,reskey,lamda=0.5,iter=200,saveloc="/tmp/hplot"):
  
  try:
    fname_clean = lfs[datakey]["clean"][reskey]
    fname_noisy = lfs[datakey]["noisy"][reskey]
  except:
    print "Key Error..."
    sys.exit()
    
  save = saveloc
  
  tv = {"lambda":lamda,"iter":iter}
  
  lf_clean = loadLF(fname_clean)
  lf_noisy = loadLF(fname_noisy)
  
  print "\nPlot now data:" 
  print fname_clean
  print fname_noisy
  print "\n"
  
  plot3LFs(lf_clean,lf_noisy,tv,save)
        
        
        
        
        
        
          


