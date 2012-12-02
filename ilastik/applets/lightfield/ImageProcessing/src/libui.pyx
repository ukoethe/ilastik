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
cpdef _colorOverlay(np.ndarray[uint_t,ndim=3] im, np.ndarray[uint_t,ndim=3] overlay, float alpha, np.ndarray[uint_t,ndim=3] result):
  
  cdef int shape_y = im.shape[0]
  cdef int shape_x = im.shape[1] 
  cdef np.ndarray[int_t, ndim=1] tmp = np.zeros(3,dtype=np.int32)
  
  
  assert shape_y == overlay.shape[0], "dimension error"
  assert shape_x == overlay.shape[1], "dimension error"  
  assert shape_y == result.shape[0], "dimension error"
  assert shape_x == result.shape[1], "dimension error"    
  
  cdef index_t i,j,c
  
  for i in range(shape_y):
    for j in range(shape_x):
      for c in range(3):
        tmp[c] = im[i,j,c]+<int>(alpha*<float>overlay[i,j,c])
        if tmp[c]  > 255:
          tmp[c] = 255
        elif tmp[c] < 0:
          tmp[c] = 0
    
        result[i,j,c] = <unsigned int>tmp[c]