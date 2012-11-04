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


  


#@cython.boundscheck(False)
#def pixelMultiplication(np.ndarray[DTYPE_t, ndim=2] f, np.ndarray[DTYPE_t, ndim=2] g):
#	if g.shape[0] % 2 != 0 or g.shape[1] % 2 != 0:
#		raise ValueError("Only even dimensions on filter supported")
#	assert f.dtype == DTYPE and g.dtype == DTYPE
#    
#	cdef int sy = f.shape[0]
#	cdef int sx = f.shape[1]
#    
#	cdef np.ndarray[DTYPE_t, ndim=2] h = np.zeros([sy, sx], dtype=DTYPE)
#	cdef unsigned int x, y
#
#	cdef DTYPE_t value
#		
#	for x in range(sy):
#		for y in range(sx):
#			value = f[<unsigned int>y,<unsigned int>x]*exp(-g[<unsigned int>y,<unsigned int>x])
#			h[<unsigned int>x, <unsigned int>y] = value
#	return h
