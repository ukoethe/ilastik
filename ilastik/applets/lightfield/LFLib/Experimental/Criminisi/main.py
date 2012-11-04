from LFLib.ImageProcessing.ui import show
from segmentate import *
from scipy.misc import imread
import scipy.ndimage as nd
from libcriminisi import _thinOutLabels


def runCriminisi(fname="./epi2.png",fromDisp=1.5,toDisp=-0.5,steps=121,stdThreshold=20):
  
  epi = loadSingleEpi(fname)
  if len(epi.shape) == 2:
    tmp = np.zeros((epi.shape[0],epi.shape[1],3),dtype=np.uint8)
    for i in range(3):
      tmp[:,:,i] = epi[:,:]
    epi = tmp
    
  channels = epi.shape[2]
  
  #create mask
  mask = np.zeros((epi.shape[0],epi.shape[1],channels),dtype=np.uint8)
  
  n=0
  while True:
    #calc mean and standard deviation over disparity space
    meanSpace,stdSpace,shifts = getStatisticSpaces(epi,mask,fromDisp,toDisp,steps)
    
    #create a label layer 
    labeled = labelMinStdDevs(stdSpace,stdThreshold,1)
    
    #closing of small gaps
    nd.grey_closing(input=labeled, size=(5,5), output=labeled)
    
    #thin out the labels
    labeled,shiftIndices = _thinOutLabels(labeled.astype(np.uint8),stdSpace.astype(np.float32))
    
    for i in range(epi.shape[1]):
      if shiftIndices[i] != -1:
        print "shift at pixel",i,"was",shifts[shiftIndices[i]]
      else:
        print "at pixel",i,"was no shift"
    #update mask by masking out labels
    mask = updateMask(mask,labeled,shifts,shiftIndices)
    
    #create an image with labeled layers
    view = drawLabeledLayers(stdSpace,labeled)
    
    show([epi.astype(np.uint8),meanSpace.astype(np.uint8),mask.astype(np.uint8)[:]*255,view.astype(np.uint8)])
    
    n+=1
    print "n=",n
    if n==3:
      print "break loop!"
      return
    
    

if __name__ == "__main__":

  runCriminisi()
  #testFastCriminisi()