import sys
import vigra
import h5py as h5
import numpy as np
from time import time
from LFLib.ImageProcessing.ui import show
from LFLib.LightField import *
from scipy.misc import imread,imsave,imresize
from scipy.ndimage.interpolation import rotate
import pylab as plt



path = "/home/swanner/Dropbox/GeorgievData/"
data = [path+"girl.png",path+"jeff.png",path+"seagull.png"]


class GLF(object):
  
  def __init__(self,imloc):
    
    self.im = imread(imloc)[:,:,0:3]
    self.yRes = self.im.shape[0]
    self.xRes = self.im.shape[1]
    self.lenses_x = 96
    self.lenses_y = 72
    self.maxMiSize = 69
    self.outMiSize = 9
    self.outSize = [self.lenses_y*self.outMiSize,self.lenses_x*self.outMiSize]
    self.outIm = np.zeros((self.outSize[0],self.outSize[1],3),dtype=np.uint8)
    
    self.calibrate()
    
    self.renderFocusSeries(saveTo="/home/swanner/Desktop/Test/")
  
  
  def calibrate(self,test=False):
    minCoords = [70,45]
    vec_x = 74.77
    vec_y = 74.71
    
    self.grid = np.zeros((self.lenses_y,self.lenses_x,2),dtype=np.uint32) 
    
    for y in range(self.lenses_y):
      for x in range(self.lenses_x):
        self.grid[y,x,0] = int(np.round(y*vec_y+minCoords[0]))
        self.grid[y,x,1] = int(np.round(x*vec_x+minCoords[1]))  
    
    if test:
      test = np.copy(self.im)
      for i in range(self.lenses_y):
        for j in range(self.lenses_x):
          test[self.grid[i,j][0]-1,self.grid[i,j][1]-1,:]=0
          test[self.grid[i,j][0]-1,self.grid[i,j][1]+1,:]=0
          test[self.grid[i,j][0],self.grid[i,j][1],:]=0
          test[self.grid[i,j][0]+1,self.grid[i,j][1]-1,:]=0
          test[self.grid[i,j][0]+1,self.grid[i,j][1]+1,:]=0
      show([test])
      
      
  def cutPatch(self,i,j,miSize,miShift):
    pos = (self.grid[i,j,0],self.grid[i,j,1])
    patch = self.im[pos[0]-(miSize-1)/2:pos[0]+(miSize-1)/2+1,pos[1]-(miSize-1)/2:pos[1]+(miSize-1)/2+1,:]
    return imresize(patch,(self.outMiSize,self.outMiSize,3))
    
    
      
  def renderImage(self,miSize=69,miShift=[0,0]):
    if miSize>self.maxMiSize:
      print "micro image size overlap!"
      return
    
    for i in range(self.lenses_y):
      for j in range(self.lenses_x):
        patch = self.cutPatch(i,j,miSize,miShift)
        for c in range(3):
          self.outIm[i*self.outMiSize:(i+1)*self.outMiSize,j*self.outMiSize:(j+1)*self.outMiSize,c] = np.flipud(np.fliplr(patch[:,:,c]))
          
      
      
  def renderFocusSeries(self,fromSize=5,toSize=29,saveTo="/tmp/gfs"):
    if saveTo[-1] != "/":
      saveTo+="/"
      
    size = fromSize
    n=0
    for i in range((toSize-fromSize)/2+1):
      print "render image",n,"from",(toSize-fromSize)/2+1
      self.renderImage(miSize=size)
      path = saveTo+"focusseries_%3.3i.png"%(n)
      imsave(path,self.outIm)
      size += 2
      n+=1
      
        
     

