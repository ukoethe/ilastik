import cython
import numpy as np
cimport numpy as np
  
ctypedef np.float32_t float_t
ctypedef Py_ssize_t index_t


@cython.boundscheck(False)
@cython.wraparound(False)
def _chooseEigenVectors(np.ndarray[float_t, ndim=3] evals, np.ndarray[float_t, ndim=3] evecs1, np.ndarray[float_t, ndim=3] evecs2, np.ndarray[float_t, ndim=3] o):

  cdef int shape_0 = evals.shape[0]
  cdef int shape_1 = evals.shape[1]
  cdef index_t i,j
  
  for i in range(shape_0):
    for j in range(shape_1):
      if evals[i,j,0] < evals[i,j,1]:
        o[i,j,0] = evecs1[i,j,0]
        o[i,j,1] = evecs1[i,j,1]
      else:
        o[i,j,0] = evecs2[i,j,0]
        o[i,j,1] = evecs2[i,j,1]