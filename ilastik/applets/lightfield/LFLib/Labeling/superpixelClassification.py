import sys
import vigra
import h5py as h5
import numpy as np
from time import time
from LFLib.ImageProcessing.ui import show
from LFLib.LightField import *
from LFLib.LFDepth.depth import *
from scipy.misc import *
import pylab as plt

import slic
from skimage.measure import regionprops
from LFLib.ImageProcessing.improc import colorRange

from classification import Classifier




class SuperPixelClassifier(Classifier):
  
  def __init__(self,lf,labels,view,treeCount=40,min_split_node_size=100,spcount=100,workingDir=None,resultDir=None):
    
    Classifier.__init__(self,lf,labels,view,treeCount,min_split_node_size,workingDir,resultDir)
    
    self.debug = False
    self.spcount = spcount
        
    self.playground()
    
   
   
   
   
  def playground(self):
    pass
    
  



############################################################################################################
############################################################################################################
############                      F E A T U R E   H E L P E R S                              ###############
    
  def getPropertyImage(self,probs,regions,name):
    img = np.zeros((self.lf.yRes,self.lf.xRes),dtype=np.float32)
    for prob in probs:
      val = prob[name]
      label = prob["Label"]
      indices = np.where(regions==label)
      img[indices] = val
    return img
   
   
  def getSuperpixel(self,img,size):
    if img.dtype != np.uint8:
      img = colorRange(img[:]).astype(np.uint8)
    
    if len(img.shape)==3 and img.shape[2]==3:
      image_argb = np.dstack([img[:,:,:1],img[:]]).copy("C")
    elif len(img.shape)==3 and img.shape[2]==1:
      image_argb = np.dstack([img[:,:,0],img[:,:,0],img[:,:,0],img[:,:,0]]).copy("C")
    elif len(img.shape)==2:
      image_argb = np.dstack([img,img,img,img]).copy("C")
      
    region_labels = slic.slic_n(image_argb, size, 8)
    if self.debug:
      slic.contours(image_argb, region_labels, 8)
      show([image_argb[:,:,1:].astype(np.uint8)])
    return region_labels
  
  
  def calcRegionMeanIntensity(self,img,regions):
    if self.debug:
      print "calcRegionMeanIntensity...",
    if len(img.shape)==3 and img.shape[2]==3:
      img = [img[:,:,0],img[:,:,1],img[:,:,2]]
    else:
      img = [img]
    
    tmp = []
    for i in range(len(img)):
      props = regionprops(regions,properties=['MeanIntensity'],intensity_image=img[i])
      tmp.append(self.getPropertyImage(props,regions, 'MeanIntensity'))
        
    if self.debug:
      if len(tmp)==3 and tmp[0].shape[2]==3:
        im = np.zeros((self.lf.yRes,self.lf.xRes,3),dtype=np.uint8)
        for i in range(3):
          im[:,:,i] = tmp[i][:]
      else:
        im = np.zeros((self.lf.yRes,self.lf.xRes),dtype=np.uint8)
        im = tmp[0]
      show([im])
    return tmp
  
  
  def calcRegionDepthRange(self,depth,regions):
    if self.debug:
      print "calcRegionDepthRange...",
    depth = colorRange(depth).astype(np.uint8)
    props = regionprops(regions,properties=['MinIntensity'],intensity_image=depth)
    mins = self.getPropertyImage(props,regions,'MinIntensity')
    props = regionprops(regions,properties=['MaxIntensity'],intensity_image=depth)
    maxs = self.getPropertyImage(props,regions,'MaxIntensity')
    tmp = maxs[:]-mins[:]
    if self.debug:
      show([maxs,mins,tmp])
    return [tmp]
  





############################################################################################################
############################################################################################################
############                      F E A T U R E H A N D L I N G                              ###############

  def calcRegionMeanColorFeature(self,img,depth,size):
    regions = self.getSuperpixel(depth,size)
    return self.calcRegionMeanIntensity(img,regions)
  
  
  def addRegionMeanColorFeature(self,size=None):
    if size is None:
      size = self.spcount
    self.featureStack.append({"type":"regionMeanColor","size":size})
    self.featureChannels.append("regionMeanIntensity r - size: "+str(size))
    self.featureChannels.append("regionMeanIntensity g - size: "+str(size))
    self.featureChannels.append("regionMeanIntensity b - size: "+str(size))
    if self.useGT:
      self.updateTrainingFeatures(self.calcRegionMeanColorFeature(self.timg,self.lf.gt[self.view[0],self.view[1],:,:],size))
    else:
      self.updateTrainingFeatures(self.calcRegionMeanColorFeature(self.timg,self.lf.depth[self.view[0],self.view[1],:,:],size))
    
    
  def calcRegionMeanDepthFeature(self,depth,size):
    regions = self.getSuperpixel(depth,size)
    return self.calcRegionMeanIntensity(depth,regions)
  
  
  def addRegionMeanDepthFeature(self,size=None):
    if size is None:
      size = self.spcount
    self.featureStack.append({"type":"regionMeanDepth","size":size})
    self.featureChannels.append("regionMeanDepth - size: "+str(size))
    if self.useGT:
      self.updateTrainingFeatures(self.calcRegionMeanColorFeature(self.lf.gt[self.view[0],self.view[1],:,:],self.lf.depth[self.view[0],self.view[1],:,:],size))
    else:
      self.updateTrainingFeatures(self.calcRegionMeanColorFeature(self.lf.depth[self.view[0],self.view[1],:,:],self.lf.depth[self.view[0],self.view[1],:,:],size))
    
    
  
  def calcDepthRangeFeature(self,depth,size):
    regions = self.getSuperpixel(depth,size)
    return self.calcRegionDepthRange(depth,regions)
  
  
  def addDepthRangeFeature(self,size=None):
    if size is None:
      size = self.spcount
    self.featureStack.append({"type":"depthRange","size":size})
    self.featureChannels.append("depthRange - size: "+str(size))
    if self.useGT:
      self.updateTrainingFeatures(self.calcDepthRangeFeature(self.lf.gt[self.view[0],self.view[1],:,:],size))
    else:
      self.updateTrainingFeatures(self.calcDepthRangeFeature(self.lf.depth[self.view[0],self.view[1],:,:],size))
    
    
  def calcFeatures(self,img,depth,view):
    tmp_features = np.zeros((self.lf.yRes,self.lf.xRes,len(self.featureChannels)),dtype=np.float32)
    tmp = []
    for feature in self.featureStack:
      if feature["type"] == "color":
        tmp+=self.calcColorFeature(img,feature["size"])
      if feature["type"] == "texture":
        tmp+=self.calcTextureFeature(self.rgb2bw(img),feature["size"])
      if feature["type"] == "edge":
        tmp+=self.calcEdgeFeature(self.rgb2bw(img),feature["size"])
      if feature["type"] == "laplace":
        tmp+=self.calcLaplacianFeature(self.rgb2bw(img),feature["size"])
      if feature["type"] == "hessianEV":
        tmp+=self.calcHessianEVFeature(self.rgb2bw(img),feature["size"])
      if feature["type"] == "rgbd":
        tmp+=self.calcRGBDFeature(img,depth,feature["size"])
      if feature["type"] == "stEV":
        tmp+=self.calcStructureTensorEVFeature(feature["size"],view)
      if feature["type"] == "regionMeanColor":
        tmp+=self.calcRegionMeanColorFeature(img,depth,feature["size"])
      if feature["type"] == "depthRange":
        tmp+=self.calcDepthRangeFeature(depth,feature["size"])
      if feature["type"] == "depth":
        tmp+=self.calcDepthFeature(depth,feature["size"])
      if feature["type"] == "regionMeanDepth":
        tmp+=self.calcRegionMeanDepthFeature(depth,feature["size"])
        
    for i in range(len(tmp)):
      tmp_features[:,:,i] = tmp[i][:]
        
    return tmp_features.reshape((self.lf.yRes*self.lf.xRes,len(self.featureChannels)))
    
    
    
    
    