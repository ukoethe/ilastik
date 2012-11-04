from scipy.misc import imread,imsave
from ImageProcessing.ui import show
from ImageProcessing.improc import colorRange
import scipy.ndimage as nd
from LightField import *
import numpy as np
import vigra
import glob


def getImages(loc,sizeReduce=1.0):
  print "search at location:",loc+"/*.png"
  
  files = []
  try:
    for f in glob.glob(loc+"/*.png"):
      files.append(f)
    files.sort()
    files.reverse()
  except Exception as e:
    print e
    print "Files not found"
    return None
  

  images=[]
  for f in files:
    print f
    im = imread(f)
    if sizeReduce != 1.0:
      print "size reduce factor:",sizeReduce," resize to:",int(im.shape[0]/sizeReduce),int(im.shape[1]/sizeReduce)
      for c in range(3):
        im[:,:,c] = nd.interpolation.zoom(im[:,:,c],2)
      im = vigra.sampling.resize(im,(int(im.shape[0]/sizeReduce),int(im.shape[1]/sizeReduce)))
      im = colorRange(im)
    im = np.transpose(im.view(np.ndarray))
    im = im[:,:,0:3]
    images.append(im)
      
    return images

def fromStanford(imgloc):
  
  imgs = getImages(imgloc)