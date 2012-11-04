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
cpdef _div(np.ndarray[float_t,ndim=2] xi_y, np.ndarray[float_t,ndim=2] xi_x):
  
  cdef int shape_y = xi_y.shape[0]
  cdef int shape_x = xi_y.shape[1] 
  cdef np.ndarray[float_t, ndim=2] div = np.zeros_like(xi_y)
  
  cdef float term1,term2
  
  cdef index_t i,j
  
  for i in range(shape_y):
    for j in range(shape_x):
      
      if i > 0 and i < shape_y-1:
        term1 = xi_y[i,j] - xi_y[i-1,j]    
      elif i == 0:
        term1 = xi_y[i,j]       
      elif i == shape_y-1: 
        term1 = -xi_y[i-1,j]  
      
      if j > 0 and j < shape_x-1:
        term2 = xi_x[i,j] - xi_x[i,j-1]
      elif j == 0:
        term2 = xi_x[i,j]
      elif j == shape_x-1:
        term2 = -xi_x[i,j-1]
        
      div[i,j] = term1+term2
      
       
  return div





@cython.boundscheck(False)
@cython.wraparound(False)
cpdef _grad(np.ndarray[float_t,ndim=2] u):
  
  cdef int shape_y = u.shape[0]
  cdef int shape_x = u.shape[1] 
  cdef np.ndarray[float_t, ndim=2] gy = np.zeros((shape_y,shape_x), dtype=np.float32)
  cdef np.ndarray[float_t, ndim=2] gx = np.zeros((shape_y,shape_x), dtype=np.float32)
  
  cdef index_t i,j
  
  for i in range(shape_y):
    for j in range(shape_x):
      if i<shape_y-1:
        gy[i,j] = u[i+1,j]-u[i,j]
      elif i==shape_y-1:
        gy[i,j] = 0
      if j<shape_x-1:
        gx[i,j] = u[i,j+1]-u[i,j]
      elif j==shape_x-1:
        gx[i,j] = 0
      
  return gy,gx




@cython.boundscheck(False)
@cython.wraparound(False)
cpdef _normP(np.ndarray[float_t,ndim=2] xi_y, np.ndarray[float_t,ndim=2] xi_x):
  
  cdef int shape_y = xi_y.shape[0]
  cdef int shape_x = xi_y.shape[1]
  cdef index_t i,j
  cdef float tmp
  
  cdef np.ndarray[float_t, ndim=2] xi_out_x = np.zeros((shape_y,shape_x), dtype=np.float32)
  cdef np.ndarray[float_t, ndim=2] xi_out_y = np.zeros((shape_y,shape_x), dtype=np.float32)
  
  for i in range(shape_y):
    for j in range(shape_x):
      tmp = sqrt(xi_y[i,j]**2+xi_x[i,j]**2)
      if tmp > 1:
        xi_out_y[i,j] = xi_y[i,j]/tmp
        xi_out_x[i,j] = xi_x[i,j]/tmp
      else:
        xi_out_y[i,j] = xi_y[i,j]
        xi_out_x[i,j] = xi_x[i,j]
  return xi_out_y,xi_out_x
  
  
  
  
@cython.boundscheck(False)
@cython.wraparound(False)
cpdef _normQ(np.ndarray[float_t,ndim=2] q, float lamda, float sigma, int p):
  
  cdef int shape_y = q.shape[0]
  cdef int shape_x = q.shape[1]
  cdef index_t i,j
  cdef float value,norm,tmp

  cdef np.ndarray[float_t, ndim=2] q_out = np.zeros((shape_y,shape_x), dtype=np.float32)
  
  for i in range(shape_y):
      for j in range(shape_x):
        
        value = q[i,j]
        
        if p==1:  
          tmp = 2*lamda*fabs(value)
          if tmp>1:
            norm = tmp
          else:
            norm = 1
        elif p==2:
          norm = (1.0+sigma*lamda)
        else:
          print "Error in _normQ, only p=1 or p=2 implemented"
          
        q_out[<unsigned int>i,<unsigned int>j] = value/norm
          
  return q_out
  
  




@cython.boundscheck(False)
@cython.wraparound(False)
cpdef _weightNormP(np.ndarray[float_t,ndim=2] weight, np.ndarray[float_t,ndim=2] xi_y, np.ndarray[float_t,ndim=2] xi_x):
  
  cdef int shape_y = xi_y.shape[0]
  cdef int shape_x = xi_y.shape[1]
  cdef index_t i,j
  cdef float tmp
  
  cdef np.ndarray[float_t, ndim=2] xi_out_x = np.zeros((shape_y,shape_x), dtype=np.float32)
  cdef np.ndarray[float_t, ndim=2] xi_out_y = np.zeros((shape_y,shape_x), dtype=np.float32)
  
  for i in range(shape_y):
    for j in range(shape_x):
      tmp = sqrt(xi_y[i,j]**2+xi_x[i,j]**2)
      if tmp > 1:
        xi_out_y[i,j] = (1-weight[i,j])*(xi_y[i,j]/tmp)
        xi_out_x[i,j] = (1-weight[i,j])*(xi_x[i,j]/tmp)
      else:
        xi_out_y[i,j] = (1-weight[i,j])*xi_y[i,j]
        xi_out_x[i,j] = (1-weight[i,j])*xi_x[i,j]
  return xi_out_y,xi_out_x





cpdef _anisotropicDiffusion(np.ndarray[np.float32_t,ndim=2] im, int iter,float kappa, float delta_t):
  """
  @summary: anisotropic diffusion
  @param im: ndarray shape=(y,x) input image
  @param iter: <int> number of iterations
  @param kappa: <float> edge preserving strength 
  @param delta_t: <float> timestep param
  @return: ndarray shape=(y,x)
  """
  cdef int size_y = im.shape[0]
  cdef int size_x = im.shape[1]
  cdef np.ndarray[float, ndim=2] diff_im = np.zeros((size_y+2,size_x+2),dtype=np.float32)
  
  #Center pixel distances.
  cdef int dx = 1
  cdef int dy = 1
  cdef float dd = sqrt(dx**2+dy**2)
  
  #directions
  cdef np.ndarray[float, ndim=2] nablaN=np.zeros_like(im)
  cdef np.ndarray[float, ndim=2] nablaS=np.zeros_like(im)
  cdef np.ndarray[float, ndim=2] nablaW=np.zeros_like(im)
  cdef np.ndarray[float, ndim=2] nablaE=np.zeros_like(im)
  cdef np.ndarray[float, ndim=2] nablaNE=np.zeros_like(im)
  cdef np.ndarray[float, ndim=2] nablaSE=np.zeros_like(im)
  cdef np.ndarray[float, ndim=2] nablaSW=np.zeros_like(im)
  cdef np.ndarray[float, ndim=2] nablaNW=np.zeros_like(im)
  
  cdef np.ndarray[float, ndim=2] cN = np.zeros_like(im)
  cdef np.ndarray[float, ndim=2] cS = np.zeros_like(im)
  cdef np.ndarray[float, ndim=2] cE = np.zeros_like(im)
  cdef np.ndarray[float, ndim=2] cW = np.zeros_like(im)
  cdef np.ndarray[float, ndim=2] cNE = np.zeros_like(im)
  cdef np.ndarray[float, ndim=2] cSE = np.zeros_like(im)
  cdef np.ndarray[float, ndim=2] cSW = np.zeros_like(im)
  cdef np.ndarray[float, ndim=2] cNW = np.zeros_like(im)
  
  cdef Py_ssize_t t
  
  #Anisotropic diffusion.
  for t from 0 <= t < iter:
    diff_im[1:size_y+1,1:size_x+1] = im[:,:]
        
    nablaN = diff_im[0:size_y,1:size_x+1]   - im;
    nablaS = diff_im[2:size_y+2,1:size_x+1] - im;
    nablaE = diff_im[1:size_y+1,2:size_x+2] - im;
    nablaW = diff_im[1:size_y+1,0:size_x]   - im;
    
    nablaNE = diff_im[0:size_y,2:size_x+2]  - im;
    nablaSE = diff_im[2:size_y+2,2:size_x+2]- im;
    nablaSW = diff_im[2:size_y+2,0:size_x]  - im;
    nablaNW = diff_im[0:size_y,0:size_x]    - im;
  
    #Diffusion function.
    cN = 1.0/(1 + (nablaN/kappa)**2)
    cS = 1.0/(1 + (nablaS/kappa)**2)
    cW = 1.0/(1 + (nablaW/kappa)**2)
    cE = 1.0/(1 + (nablaE/kappa)**2)
    cNE = 1.0/(1 + (nablaNE/kappa)**2)
    cSE = 1.0/(1 + (nablaSE/kappa)**2)
    cSW = 1.0/(1 + (nablaSW/kappa)**2)
    cNW = 1.0/(1 + (nablaNW/kappa)**2)
  
  
    #Discrete PDE solution
    im = im + delta_t*((1/(dy**2))*cN*nablaN + (1/(dy**2))*cS*nablaS + (1/(dx**2))*cW*nablaW + (1/(dx**2))*cE*nablaE + (1/(dd**2))*cNE*nablaNE + (1/(dd**2))*cSE*nablaSE + (1/(dd**2))*cSW*nablaSW + (1/(dd**2))*cNW*nablaNW )
  return im