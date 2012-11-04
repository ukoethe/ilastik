from LFLib.ImageProcessing.improc import colorRange
from LFLib.ImageProcessing.ui import show
from skimage.measure import regionprops
from scipy.misc import imread
import numpy as np
import vigra
import slic



def rgb2bw(img):
  return 0.3*img[:,:,0]+0.59*img[:,:,1]+0.11*img[:,:,2]


def getPropertyImage(res,probs,regions,name):
  img = np.zeros((res[0],res[1]),dtype=np.float32)
  for prob in probs:
    val = prob[name]
    label = prob["Label"]
    indices = np.where(regions==label)
    img[indices] = val
  return img


def regionClustering(img,depth,numOfPixels):
  depth = depth.astype(np.uint8)
  image_argb = np.dstack([depth,depth,depth,depth]).copy("C")
  region_labels = slic.slic_n(image_argb, numOfPixels, 4)
  if True:
    slic.contours(image_argb, region_labels, 8)
    show([image_argb[:,:,1:].astype(np.uint8)])
  
  if len(img.shape)==3 and img.shape[2]==3:
    channels = [img[:,:,0],img[:,:,1],img[:,:,2]]
  else:
    channels = [img]
    
  tmp = []
  for i in range(len(channels)):
    props = regionprops(region_labels,properties=['MeanIntensity'],intensity_image=channels[i])
    tmp.append(getPropertyImage([img.shape[0],img.shape[1]],props,region_labels, 'MeanIntensity'))
    
  
  props = regionprops(region_labels,properties=['MeanIntensity'],intensity_image=depth)
  md = getPropertyImage([depth.shape[0],depth.shape[1]],props,region_labels, 'MeanIntensity')

  im = np.zeros((img.shape[0],img.shape[1],3),dtype=np.uint8)
  for i in range(3):
    im[:,:,i] = tmp[i][:]
  
  return im,md


def calcSimpleWeighting(img,depth):
  
  bw = rgb2bw(img).astype(np.float32)
  
  dimg = vigra.filters.gaussianGradientMagnitude(bw,1.0)
  dd = vigra.filters.gaussianSmoothing(vigra.filters.gaussianGradientMagnitude(depth.astype(np.float32),1.0),1.2)
  cr = vigra.filters.gaussianSmoothing(vigra.analysis.cornernessHarris(bw, 1.0),1.2)
  
  crmax = np.amax(cr)
  cr /= crmax
  dimgmax = np.amax(dimg)
  dimg /= dimgmax
  ddmax = np.amax(dd)
  dd /= ddmax
  
  weights = vigra.filters.gaussianSmoothing((dimg[:]-cr[:])*dd[:],2.0)
  weightsmin = np.amin(weights)
  weights[:]-=weightsmin
  weightsmax = np.amax(weights)
  weights /= weightsmax*1.1
  weights = 1.0-weights[:]
  
  return weights


if __name__ == "__main__":
  
  img="/home/swanner/data/projects/Segmentation/screws/cv.png"
  depth="/home/swanner/data/projects/Segmentation/screws/depth_cv.png"  
  
  img=imread(img)
  depth=imread(depth)
  
  show([calcSimpleWeighting(img,depth)])