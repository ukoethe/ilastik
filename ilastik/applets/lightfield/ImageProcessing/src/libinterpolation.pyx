import cython
import numpy as np
cimport numpy as np
from time import time

cdef extern from "math.h":
  float floor(float)
  float ceil(float)
  float sqrt(float)
  float fabs(float)
  
  
ctypedef np.float32_t float_t
ctypedef np.int32_t int_t
ctypedef np.uint8_t uint_t
ctypedef Py_ssize_t index_t



@cython.boundscheck(False)
@cython.wraparound(False)
cpdef _bilinear_2d(np.ndarray[uint_t,ndim=3] source, float samplePos_y, float samplePos_x):
  #assert len(source.shape) == 3, "Shape Error: need 3d array as 2d image with value channel of len 1 or 3!"

  
  cdef np.ndarray[int_t, ndim=2] source_pixel = np.zeros((4,2), dtype=np.int32)
  cdef np.ndarray[int_t, ndim=2] source_value = np.zeros((4,source.shape[2]), dtype=np.int32)
  cdef np.ndarray[float_t, ndim=1] result_value = np.zeros(source.shape[2], dtype=np.float32)
  
  cdef float R1,R2
  cdef int floor_x,floor_y,ceil_x,ceil_y
  
  floor_x = <int>floor(<float>samplePos_x)
  floor_y = <int>floor(<float>samplePos_y)
  ceil_x = <int>ceil(<float>samplePos_x)
  ceil_y = <int>ceil(<float>samplePos_y)
  
  if ceil_x == floor_x:
    ceil_x = ceil_x+1
  if ceil_y == floor_y:
    ceil_y = ceil_y+1
  
  source_pixel[0,0] = floor_y
  source_pixel[0,1] = floor_x
  source_pixel[1,0] = floor_y
  source_pixel[1,1] = ceil_x
  source_pixel[2,0] = ceil_y
  source_pixel[2,1] = ceil_x
  source_pixel[3,0] = ceil_y
  source_pixel[3,1] = floor_x
  
  for p in range(4):
    for c in range(source.shape[2]):
      source_value[p,c] = source[source_pixel[p,0],source_pixel[p,1],c]
      
  
  for c in range(source.shape[2]):
    #R1 = Q11*(ceil_x-x)+Q12*(x-floor_x)
    R1 = <float>source_value[0,c]*(ceil_x-samplePos_x)+<float>source_value[1,c]*(samplePos_x-floor_x)
    R2 = <float>source_value[3,c]*(ceil_x-samplePos_x)+<float>source_value[2,c]*(samplePos_x-floor_x)
    result_value[c] = R1*(ceil_y-samplePos_y)+R2*(samplePos_y-floor_y)
    
  return result_value
          
          
      
  
  
  