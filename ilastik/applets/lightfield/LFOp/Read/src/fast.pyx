import cython
import numpy as np
cimport numpy as np



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
cpdef _depthToDisparity(np.ndarray[float_t, ndim=2] depth, np.ndarray[float_t, ndim=2] exM, np.ndarray[float_t, ndim=2] inM, np.ndarray[float_t, ndim=2] exM_inv, np.ndarray[float_t, ndim=2] inM_inv, float shift, float minDisp, float maxDisp):

  
  cdef int shape_y = depth.shape[0]
  cdef int shape_x = depth.shape[1]
  
  cdef np.ndarray[float_t, ndim=1] v_3 = np.zeros(3, dtype=np.float32)
  cdef np.ndarray[float_t, ndim=1] p = np.zeros(3, dtype=np.float32)
  cdef np.ndarray[float_t, ndim=1] v_3_tmp = np.zeros(3, dtype=np.float32)
  cdef np.ndarray[float_t, ndim=1] v_4 = np.zeros(4, dtype=np.float32)
  cdef np.ndarray[float_t, ndim=1] v_4_tmp = np.zeros(4, dtype=np.float32)
  
  cdef index_t n
  cdef int _y,_x,y,x
  cdef float f_ij
 
  for y in range(shape_y):
    for x in range(shape_x):
      
      _y = int(fabs(shape_y-1-y)) 
      _x = x
      
      #get current depth
      f_ij = depth[y,x]
      
      #calc current vector on image plane
      v_3[0] = _x*f_ij 
      v_3[1] = _y*f_ij
      v_3[2] = f_ij
      
      _vecMatMul(v_3,inM_inv,v_3_tmp)
      
      v_4[0] = v_3_tmp[0]
      v_4[1] = v_3_tmp[1]
      v_4[2] = v_3_tmp[2]
      v_4[3] = 1
      
      _vecMatMul(v_4,exM_inv,v_4_tmp)
      _vecMatMul(v_4_tmp,exM,v_4)
      
      v_3[0] = v_4[0]
      v_3[1] = v_4[1]
      v_3[2] = v_4[2]

      _vecMatMul(v_3,inM,v_3_tmp)
      
      p[0] = v_3_tmp[0]/v_3_tmp[2]
      p[1] = v_3_tmp[1]/v_3_tmp[2]
      p[2] = v_3_tmp[2]/v_3_tmp[2]
      p[1] = fabs(shape_y-1-p[1])


      #store difference between former and backtraced pixel and substract the main shift
      depth[y,x] = fabs(_x-p[0])-shift
      if depth[y,x] < minDisp:
        depth[y,x] = minDisp
      if depth[y,x] > maxDisp:
        depth[y,x] = maxDisp
        
        
     
        

@cython.boundscheck(False)
@cython.wraparound(False)
cdef _vecMatMul(np.ndarray[float_t, ndim=1] v, np.ndarray[float_t, ndim=2] m, np.ndarray[float_t, ndim=1] out):

  cdef int size_y, size_x
  cdef index_t i,j
  cdef float tmp1
  cdef float tmp2
  
  size_y = m.shape[0]
  size_x = m.shape[1]
  
  
  for i in range(size_x):
    tmp2 = 0
    for j in range(size_y):
      tmp1 = v[j]
      tmp2 = tmp2 + (tmp1*m[j,i])
    out[i] = tmp2
