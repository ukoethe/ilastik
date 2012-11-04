import os
import h5py as h5
import numpy as np
import scipy as sc
import scipy.misc as mi
import scipy.ndimage as nd
 
from Blender import *
from LightField import *
from LFDepth.depth import *
from ImageProcessing.ui import *
from ImageProcessing.filter import *
from ImageProcessing.interpolation import *

from Experimental.playground import *


#from settings import *
#from Experimental.fromGeorgiev import *







def getDataSet(name="screws",label="label1"):
  
  #projectLoc = "./../../../Dropbox/"
  projectLoc = "/home/swanner/data/projects/Segmentation/"
  
  if name == "screws":
    lf = loadLF(projectLoc+name+"/"+name+".h5")
    try:
      labels = np.load(projectLoc+name+"/"+label+"/labels.npy")
    except:
      labels = projectLoc+name+"/"+label+"/labels.png"
  
  
  return {"lf":lf,
          "labels":labels,
          "view":[lf.vRes/2,lf.hRes/2],
          "output":projectLoc+name+"/"+label+"/"
          } 
 
 
def testClassification(dataset="screws"): 
  
  rgb = True
  stEV = True
  tex = True
  edge = False
  D = False
  spRM = False
  spDR = True
  spRMD = True
  
  steps = 3
  initSize = 0.8
  sizeStep = 0.6
  
  
  data = getDataSet(dataset)
  from LFLib.Labeling.superpixelClassification import SuperPixelClassifier
  classifier = SuperPixelClassifier(lf=data["lf"],labels=data["labels"],view=data["view"],treeCount=160,spcount=500,workingDir=data["output"],resultDir="results")
  
  for i in range(steps):
    if rgb:
      classifier.addColorFeature(initSize+i*sizeStep)
    if stEV:
      classifier.addStructureTensorEVFeature(initSize+i*sizeStep)
    if tex:
      classifier.addTextureFeature(initSize+i*sizeStep)
    if edge:
      classifier.addEdgeFeature(initSize+i*sizeStep)
    if D:
      classifier.addDepthFeature(initSize+i*sizeStep)
    
  #classifier.addRegionMeanColorFeature(1500)
  classifier.addDepthRangeFeature()
  classifier.addRegionMeanDepthFeature()
  classifier.trainWithFeatureSelection()
  classifier.predict([4,3], output='l')











def testDepthEstimation(inner=0.8,outer=1.2):
  fname = os.getenv("HOME")+"/Dropbox/LightFields/buddha_bl02_7x7_rgb.h5"
  lf = loadLF(fname)
  calcDepth(lf,inner,outer,full=True,colorMode=1)
  showDepth(lf)
  saveLF(lf,"/home/swanner/Desktop/buddha.h5")  
  
  
def testNewDepthEstimation(inner=0.8,outer=1.0):
  fname = os.getenv("HOME")+"/Dropbox/LightFields/buddha_bl02_7x7_rgb.h5"
  lf = loadLF(fname)
  calcDepth(lf,inner,outer)
  showDepth(lf)
  
  
def testBilinear():
  im=np.zeros((2,2,3),dtype=np.uint8)
  for i in range(3):
    im[0,0,i]=50
    im[0,1,i]=100
    im[1,0,i]=150
    im[1,1,i]=200
  print "interpolation =",bilinear_2d(im,1.0,1.0)
  
  
def playground():
  lf=loadLF(lfs["buddha"]["clean"]["5x5"])
  calcDepth(lf)
  showDepth(lf)
  
  
def gui():
  import LFLib.Viewer.viewer as v
  v.show(lfs["still"]["clean"]["9x9"])
  
  
def fromGeorgievTest():
  glf = GLF(data[2])
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
  

  
  
  
  
  
  
  
  
  
  
  
  
  
  
  
if __name__ == "__main__":
  print "no tests active"
  #playground()
  #gui()
  #labelTest("buddha","board",False,True,True)
  #labelTest("buddha","stick",False,True,True)
  #labelTest("buddha","buddha",False,True,True)
  #labelTest("buddha","dices",False,True,True)
  #labelTest("buddha","column",False,True,True)
  #fromGeorgievTest()
  
  #segmentationTest(type="screws",views=[[1,1],[4,4]])
  #testClassification()