import sys
import vigra
import h5py as h5
import numpy as np
from time import time
from scipy.misc import imread,imsave
from LFLib.ImageProcessing.ui import show

import weighting



class Classifier(object):
  
  def __init__(self,lf,labels,view,treeCount=40,min_split_node_size=100,workingDir=None,resultDir=None):
    
    self.debug = True
    self.useGT = False
    
    if type(lf) == type(str("str")):
      from LFLib.LightField import loadLF
      lf = loadLF(lf)
      
    self.lf = lf
    self.view = view
    self.timg = np.copy(self.lf.lf[self.lf.vRes/2,self.lf.hRes/2,:,:,:])
    
    self.saveProbs = False
    self.saveWeights = False
    self.saveLabels = True
    self.saveFeatureSelection = False
    
    self.probabilitiesAppendix = ""
    self.labelsAppendix = ""
    
    self.labelLUT_array = np.array([
                [0.0, 0.0, 0.0],
                [255, 0.0, 0.0],
                [0.0, 255, 0.0],
                [0.0, 0.0, 255],
                [255, 255, 0.0],
                [0.0, 255, 255],
                [255, 0.0, 255],
                [0.0, 128, 128],
                [128, 128, 128]
                ])
    
    self.labelLUT = np.ndarray((self.labelLUT_array.shape[0],), np.uint32)
    for l in range(self.labelLUT.shape[0]):
      self.labelLUT[l] = self.labelLUT_array[l,0]*256**2 +self.labelLUT_array[l,1]*256+self.labelLUT_array[l,2]     
    
    self.labelInvLUT = np.array( [
                np.array([0, 0.0, 0.0]),                  
                np.array([255.0, 0.0, 0.0]),
                np.array([0.0, 255.0, 0.0]),
                np.array([0.0, 0.0, 255.0]),
                np.array([255.0, 255.0, 0.0]),
                np.array([0.0, 255.0, 255.0]),
                np.array([255.0, 0.0, 255.0]),
                np.array([0.0, 128.0, 128.0]),
                np.array([128.0, 128.0, 128.0])]).astype(np.int32)         
    
    self.labelNameLUT = {
                "1":"red",
                "2":"green",
                "3":"blue",
                "4":"yellow",
                "5":"lightblue",
                "6":"magenta",
                "7":"uglyblue",
                "8":"gray"
                }
  
    self.numOfClasses = 0
    self.numOfFeatures = 0
    self.treeCount = treeCount
    self.min_split_node_size = min_split_node_size
    self.workingDir = workingDir
    self.featureStack = []
    self.featureChannels = []
    
    self.tfeatures = np.zeros((self.lf.yRes,self.lf.xRes,0),dtype=np.float32)
    self.labels = None
    
    
    if self.lf.cvOnly:
      from LFLib.LightField import saveLF
      from LFLib.LFDepth.depth import calcDepth
      print "no entire depth field available, please set parameter..."
      inner = float(raw_input("inner scale:"))
      outer = float(raw_input("outer scale:"))
      lf.inner = inner
      lf.outer = outer
      lf.cvOnly = False
      calcDepth(lf,inner,outer,full=True)
      saveLF(lf)
    
    self.labels = self.parseLabels(labels) 
    
      
    from LFLib.Helpers import ensure_dir
    if resultDir is None:
      from datetime import datetime
      date=datetime.today()
      stamp = str(date.year)+"_"+str(date.month)+str(date.year)+"_"+str(date.hour)+str(date.minute)+str(date.second)
      self.directory = ensure_dir(self.workingDir+"results_"+stamp+"/")+"/"
    else:
      self.directory = ensure_dir(self.workingDir+resultDir)+"/"
      
      
    print "\n--------------------------------\nClassifier ready:\nnumber of classes:",self.numOfClasses,"\nworking directory:",self.directory
      
      
      
      
      
      

############################################################################################################
############################################################################################################
############                      F E A T U R E H A N D L I N G                              ###############
      
      
  def updateTrainingFeatures(self,features):
    tmp = np.zeros((self.lf.yRes,self.lf.xRes,self.tfeatures.shape[2]+len(features)),dtype=np.float32)
    tmp[:,:,0:self.tfeatures.shape[2]] = self.tfeatures[:,:,:]
    for i in range(len(features)):
      tmp[:,:,self.tfeatures.shape[2]+i] = features[i][:,:]
    self.tfeatures = tmp
    
  
  def rgb2bw(self,img):
    return 0.3*img[:,:,0]+0.59*img[:,:,1]+0.11*img[:,:,2]
    
    
  def calcColorFeature(self,img,size):
    tmp = []
    for i in range(self.lf.channels):
      tmp.append(vigra.filters.gaussianSmoothing(img[:,:,i].astype(np.float32),size))
    return tmp
  
      
  def addColorFeature(self,size):
    self.featureStack.append({"type":"color","size":size})
    self.featureChannels.append("color r - size: "+str(size))
    self.featureChannels.append("color g - size: "+str(size))
    self.featureChannels.append("color b - size: "+str(size))
    self.updateTrainingFeatures(self.calcColorFeature(self.timg,size))
    
    
  def calcTextureFeature(self,img,size):
    tmp = []
    res = vigra.filters.gaussianSmoothing(img[:,:].astype(np.float32),size)
    res = np.sqrt(np.abs(vigra.filters.gaussianSmoothing(img[:,:].astype(np.float32)**2, size) - res**2))
    tmp.append(res)
      
    return tmp
    
    
  def addTextureFeature(self,size):
    self.featureStack.append({"type":"texture","size":size})
    self.featureChannels.append("tex - size: "+str(size))
    self.updateTrainingFeatures(self.calcTextureFeature(self.rgb2bw(self.timg),size))
    
    
  def calcEdgeFeature(self,img,size):
    return [vigra.filters.gaussianGradientMagnitude(img.astype(np.float32),size)]
  
   
  def addEdgeFeature(self,size):
    self.featureStack.append({"type":"edge","size":size})
    self.featureChannels.append("edge - size: "+str(size))
    self.updateTrainingFeatures(self.calcEdgeFeature(self.rgb2bw(self.timg),size))
    
  
  def calcLaplacianFeature(self,img,size):
    return [vigra.filters.laplacianOfGaussian(img.astype(np.float32),size)]
  
   
  def addLaplacianFeature(self,size):
    self.featureStack.append({"type":"laplace","size":size})
    self.featureChannels.append("laplace - size: "+str(size))
    self.updateTrainingFeatures(self.calcLaplacianFeature(self.rgb2bw(self.timg),size))
    
  
  def calcHessianEVFeature(self,img,size):
    tmp = vigra.filters.hessianOfGaussianEigenvalues(img.astype(np.float32),size)
    return [tmp[:,:,0],tmp[:,:,1]]
  
   
  def addHessianEVFeature(self,size):
    self.featureStack.append({"type":"hessianEV","size":size})
    self.featureChannels.append("hessianEV 1 - size: "+str(size))
    self.featureChannels.append("hessianEV 1 - size: "+str(size))
    self.updateTrainingFeatures(self.calcHessianEVFeature(self.rgb2bw(self.timg),size))
    
    
    
  def calcStructureTensorEVFeature(self,size,view):
    tmp = []
    
    vol = self.lf.lf[view[0],:,:,:,:]
    vol = 0.3*vol[:,:,:,0]+0.59*vol[:,:,:,1]+0.11*vol[:,:,:,2]
    st = vigra.filters.structureTensorEigenvalues(vol.astype(np.float32),0.7,size)
    for i in range(3):
      tmp.append(st[view[1],:,:,i]) 

    vol = self.lf.lf[:,view[1],:,:,:]
    vol = 0.3*vol[:,:,:,0]+0.59*vol[:,:,:,1]+0.11*vol[:,:,:,2]
    st = vigra.filters.structureTensorEigenvalues(vol.astype(np.float32),0.7,size)
    for i in range(3):
      tmp.append(st[view[0],:,:,i])

    
    return tmp
  
   
  def addStructureTensorEVFeature(self,size):
    self.featureStack.append({"type":"stEV","size":size})
    for i in range(6):
      self.featureChannels.append("stEV component "+str(i+1)+" - size: "+str(size))
    self.updateTrainingFeatures(self.calcStructureTensorEVFeature(size,self.view))
    
    
  def calcDepthFeature(self,depth,size):
    return [vigra.filters.gaussianSmoothing(depth,size)]
  
  
  def addDepthFeature(self,size):
    self.featureStack.append({"type":"depth","size":size})
    self.featureChannels.append("depth - size: "+str(size))
    if self.useGT:
      self.updateTrainingFeatures(self.calcDepthFeature(self.lf.gt[self.view[0],self.view[1],:,:],size))
    else:
      self.updateTrainingFeatures(self.calcDepthFeature(self.lf.depth[self.view[0],self.view[1],:,:],size))
    
    
  def calcRGBDFeature(self,img,depth,size):
    d = vigra.filters.gaussianSmoothing(depth,size)
    im = np.zeros((img.shape[0],img.shape[1],self.lf.channels),dtype=np.float32)
    imin = np.amin(d)
    imax = np.amax(d)
    d = (d[:]-imin)/(imax-imin)
    
    for i in range(self.lf.channels):
      im[:,:,i] = vigra.filters.gaussianSmoothing(img[:,:,i].astype(np.float32),size)*d[:]
      
    return [im[:,:,0],im[:,:,1],im[:,:,2]]
    
    
  def addRGBDFeature(self,size):
    self.featureStack.append({"type":"rgbd","size":size})
    self.featureChannels.append("rgbd rd - size: "+str(size))
    self.featureChannels.append("rgbd gd - size: "+str(size))
    self.featureChannels.append("rgbd bd - size: "+str(size))
    if self.useGT:
      self.updateTrainingFeatures(self.calcRGBDFeature(self.timg,self.lf.gt[self.view[0],self.view[1],:,:],size)) 
    else:
      self.updateTrainingFeatures(self.calcRGBDFeature(self.timg,self.lf.depth[self.view[0],self.view[1],:,:],size)) 
    
  
  
    
    
    
    
    
    
    
  def getTrainingFeatures(self):
    indices = np.nonzero(self.labels)
    tlabels = np.atleast_2d(self.labels[indices]).reshape((len(indices[0]),1))
    tfeatures = np.atleast_2d(self.tfeatures[indices])
    return tlabels,tfeatures
  
  
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
      if feature["type"] == "depth":
        tmp+=self.calcDepthFeature(depth,feature["size"])
        
    for i in range(len(tmp)):
      tmp_features[:,:,i] = tmp[i][:]
        
    return tmp_features.reshape((self.lf.yRes*self.lf.xRes,len(self.featureChannels)))







############################################################################################################
############################################################################################################
############                      T R A I N  &  P R E D I C T                                ###############


  def trainWithFeatureSelection(self):
    print "\ntrain with feature selection classifier...",
    t0 = time()
    self.classifier = vigra.learning.RandomForest(self.treeCount, min_split_node_size=self.min_split_node_size) 
    tlabels,tfeatures = self.getTrainingFeatures()
    print tlabels.shape,tfeatures.shape
    oob,importance = self.classifier.learnRFWithFeatureSelection(tfeatures,tlabels)
    print 'outOfBag Error:', oob,
    
    if self.saveFeatureSelection:
      import pylab
      pylab.plot(importance[:,1])
      pylab.savefig(self.directory+"importance.png")
      self.saveClassInfos()
    print " ok! ",time()-t0,"s"
    
    return oob
    
  
  def train(self):
    print "\ntrain classifier...",
    t0 = time()
    self.classifier = vigra.learning.RandomForest(self.treeCount) 
    tlabels,tfeatures = self.getTrainingFeatures()
    oob = self.classifier.learnRF(tfeatures,tlabels)
    print 'outOfBag Error:', oob, 
    print " ok! ",time()-t0,"s"
    
    
  def predict(self,view=None):
    print "\npredict...",
    t0 = time()
    probs =[]
    weights =[]
    labels = []
    views = []
    
    if view is None:
      print ""
      for i in range(self.lf.vRes):
        for j in range(self.lf.hRes):
          views.append([i,j])
    else:
      views = [view]
    
    for v in views:
      print "predict view:",str(v)
      img = self.lf.lf[v[0],v[1],:,:,:]
      
      if self.useGT:
        depth = self.lf.gt[v[0],v[1],:,:] 
      else:
        depth = self.lf.depth[v[0],v[1],:,:]
        
      weights.append(weighting.calcSimpleWeighting(img,depth))
      
      features = self.calcFeatures(img,depth,v)
      
      probs.append(self.classifier.predictProbabilities(features))
      labels.append(self.classifier.predictLabels(features))
        
    self.saveResults(probs,labels,weights,views)
      
    print "ok! ",time()-t0,"s"
      
      
      
      
      
      
      
      
      
      
############################################################################################################
############################################################################################################
############                             H E L P E R S                                       ###############
      
        
  def saveResults(self,probs,labels,weights,views):
    if len(views) > 1:
      fname = self.directory+"probabilities"+self.probabilitiesAppendix+".h5"
      print "save entire probability field at:",fname
      fp = h5.File(fname)
      dsp = fp.create_dataset("Probabilities",data=np.zeros((self.lf.vRes,self.lf.hRes,self.lf.yRes,self.lf.xRes,self.numOfClasses),dtype=np.float32))
      ws = fp.create_dataset("Weights",data=np.ones((self.lf.vRes,self.lf.hRes,self.lf.yRes,self.lf.xRes),dtype=np.float32))
      fp.attrs["vRes"]=self.lf.vRes
      fp.attrs["hRes"]=self.lf.hRes
      fp.attrs["yRes"]=self.lf.yRes
      fp.attrs["xRes"]=self.lf.xRes
      fp.attrs["labels"]=self.numOfClasses
      
      fname = self.directory+"labeled"+self.labelsAppendix+".h5"
      print "save entire label field at:",fname
      fl = h5.File(fname)
      dsl = fl.create_dataset("Labels",data=np.zeros((self.lf.vRes,self.lf.hRes,self.lf.yRes,self.lf.xRes)),dtype=np.uint8)
      fl.attrs["vRes"]=self.lf.vRes
      fl.attrs["hRes"]=self.lf.hRes
      fl.attrs["yRes"]=self.lf.yRes
      fl.attrs["xRes"]=self.lf.xRes
      fl.attrs["labels"]=self.numOfClasses
    
    for n in range(len(probs)):
      if len(views) > 1:
        dsp[views[n][0],views[n][1],:,:,:] = probs[n][:,:].reshape((self.lf.yRes,self.lf.xRes,self.numOfClasses))
        ws[views[n][0],views[n][1],:,:] = weights[n][:,:]
        if len(probs)/2-1 == n:
          print "save views at index:",len(probs)/2,n
          if self.saveProbs:
            self.saveProbabilitiesImgs(probs[n],views[n])
          if self.saveLabels:
            self.saveLabelImg(labels[n],views[n])
          if self.saveWeights:
            self.saveWeights(weights[n],views[n])
          
        dsl[views[n][0],views[n][1],:,:] = labels[n][:].reshape((self.lf.yRes,self.lf.xRes))
      else:
        if self.saveProbs:
          self.saveProbabilitiesImgs(probs[0],views[0])
        if self.saveLabels:
          self.saveLabelImg(labels[0],views[0])
        if self.saveWeights:
          self.saveWeights(weights[0],views[0])
    
    if len(views) > 1:
      fp.close()
      fl.close()


      
  def saveLabelImg(self,label,view):
    fname = self.directory+"labeled"+self.labelsAppendix+".png"
    print "save labels to:",fname
    
    img = np.zeros((self.lf.yRes,self.lf.xRes,3),dtype=np.uint8)
    prediction = label[:].reshape((self.lf.yRes,self.lf.xRes))
    
    lut = self.labelInvLUT
    
    for c in range(3):
      img[:,:,c] = lut[:,c][(prediction[:,:]).astype(np.int32)]
    
    imsave(fname,img)
    
  
  def saveProbabilitiesImgs(self,prob,view):
    import matplotlib.cm as cm
        
    lut = cm.jet(np.arange(256))    
        
    prob_img = prob.reshape(self.lf.yRes, self.lf.xRes,self.numOfClasses)
    fsorted = np.sort(prob_img, axis = 2)                
    certainty = fsorted[:,:,-1] - fsorted[:,:,-2]
    
    
    img = np.zeros((self.lf.yRes,self.lf.xRes,3),dtype=np.uint8)
    
    fname = self.directory+"certainty_view_%i_%i.png"%(view[0],view[1])
    
    for c in range(3):
      img[:,:,c] = lut[:,c][(certainty[:,:]*255).astype(np.int32)]*255
        
    imsave(fname,img)
    
    
    
    for i in range(self.numOfClasses):
      img = np.zeros((self.lf.yRes,self.lf.xRes,3),dtype=np.uint8)

      fname = self.directory+"probabilityClass_"+self.labelNameLUT[str(i+1)]+"_view_%i_%i"+self.probabilitiesAppendix+".png"%(view[0],view[1])
      
      for c in range(3):
        img[:,:,c] = lut[:,c][(prob_img[:,:,i]*255).astype(np.int32)]*255
      
      imsave(fname,img)
  
  
  def saveWeights(self,img,view):
    fname = self.directory+"weights.png"
    print "save weights to:",fname
    
    tmp = np.zeros((self.lf.yRes,self.lf.xRes,3),dtype=np.uint8)
    
    import matplotlib.cm as cm
        
    lut = cm.jet(np.arange(256)) 
    
    for c in range(3):
      tmp[:,:,c] = lut[:,c][(img[:,:]*255).astype(np.int32)]*255
        
    imsave(fname,tmp)
  
  
  def saveClassInfos(self):
    fname = self.directory+"logfile"
    f = open(fname,"w")
    for n,info in enumerate(self.featureChannels):
      f.writelines(str(n) + " : " + info + "\n")
      
  
  def parseLabels(self,loc):
    if self.debug:
      print "parseLabels"
      
    img = imread(loc).astype(np.uint32)
       
    labels = np.zeros((img.shape[0],img.shape[1]),dtype=np.uint32)
    
    usedClasses = []
    for i in range(self.labelLUT.shape[0]):
      usedClasses.append(0)
    
    img2 = img[:,:,0]*256**2 + img[:,:,1]*256 + img[:,:,2]
    img2 = img2.astype(np.int32)
     
    
    for l in range(1,self.labelLUT.shape[0]):
      labels = np.where(img2 == self.labelLUT[l],l, labels)
      if (img2 == self.labelLUT[l]).any():
        usedClasses[l] = 1
                   
              
    self.numOfClasses = np.sum(usedClasses)
      
    return labels
      
