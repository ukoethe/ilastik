from __future__ import division
import cython
import numpy as np
cimport numpy as np

cdef extern from "math.h":
  float floor(float)
  float ceil(float)
  float sqrt(float)
  float fabs(float)
  float exp(float)
  

DTYPE = np.float
ctypedef np.float32_t float_t
ctypedef np.int_t int_t
ctypedef np.uint8_t uint_t


@cython.boundscheck(False)
def _thinOutLabels(np.ndarray[uint_t, ndim=2] labels,np.ndarray[float_t, ndim=2] stds):
  
  cdef float value
  cdef int sy,sx,index,height,lastPixel,firstPixel,gap,tmp
  
  cdef np.ndarray[int_t, ndim=1] shiftIndices = np.zeros(labels.shape[1], dtype=int)
  
  sy = labels.shape[0]
  sx = labels.shape[1]
  
  for x in range(sx):
    value = 1000000
    index = -1
    height = 0
    lastPixel = 0
    firstPixel = -1
    gap = 0
    
    #print "\n------------- new column",x,"--------------\n"
    #analyze label column
    for y in range(sy):     
      if labels[y,x] != 0:  #if label exist,
        height += 1         #update height of label column 
        
        if firstPixel==-1:  #check if it is the first label
          firstPixel=y
          #print "+++++++++++++ set first pixel to:",firstPixel
        
        lastPixel = y       #and assume it is the last one
        
        #print "y=",y,"is a label"
        if y+1 != firstPixel+height:  #check if all labels are connected, if not mark a gap 
          #print "<------------ here is a gap"
          gap = 1
          
        if stds[y,x] < value: #if value of std is smallest remind it as well as index
          value = stds[y,x]
          index = y
    
    #print "++++++++++++ last pixel is:",lastPixel
          
    #modify label column
    if height > 1: #if column has more than one label,
      if gap == 0: #and if there is no gap,
        tmp = index
        if height%2==0:
          index = <unsigned int>(firstPixel+(lastPixel-firstPixel)/2+1)  #shift smallest index to the middle of the block
        else:
          index = <unsigned int>(firstPixel+(lastPixel-firstPixel)/2)  #shift smallest index to the middle of the block
        #print "shift index from",tmp,"to",index 

    shiftIndices[x] = index
          
    for y in range(sy):
      if y != index:
        labels[y,x] = 0
        
  return labels,shiftIndices