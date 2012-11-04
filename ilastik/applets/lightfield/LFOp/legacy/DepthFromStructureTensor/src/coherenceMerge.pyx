import cython
import numpy as np
cimport numpy as np
  
ctypedef np.float32_t float_t
ctypedef Py_ssize_t index_t


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef _coherenceMerge(np.ndarray[float_t,ndim=4] c1, np.ndarray[float_t,ndim=4] c2, np.ndarray[float_t,ndim=4] d1, np.ndarray[float_t,ndim=4] d2):
  
  cdef int shape_u = c1.shape[0]
  cdef int shape_v = c1.shape[1]
  cdef int shape_y = c1.shape[2]
  cdef int shape_x = c1.shape[3] 
  
  cdef np.ndarray[float_t, ndim=4] res_c = np.zeros((shape_u,shape_v,shape_y,shape_x), dtype=np.float32)
  cdef np.ndarray[float_t, ndim=4] res_d = np.zeros((shape_u,shape_v,shape_y,shape_x), dtype=np.float32)
  cdef index_t u,v,y,x

  for u in range(shape_u):
    for v in range(shape_v):
      for y in range(shape_y):
        for x in range(shape_x):
          if c1[u,v,y,x] >= c2[u,v,y,x]:
            res_c[u,v,y,x] = c1[u,v,y,x]
            res_d[u,v,y,x] = d1[u,v,y,x]
          else:
            res_c[u,v,y,x] = c2[u,v,y,x]
            res_d[u,v,y,x] = d2[u,v,y,x]
  return res_d,res_c