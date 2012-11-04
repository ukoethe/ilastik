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
def _colormap(np.ndarray[uint_t,ndim=2] gray_in, np.ndarray[float_t,ndim=2] cmap):
  
  cdef int shape_y = gray_in.shape[0]
  cdef int shape_x = gray_in.shape[1] 
  cdef np.ndarray[uint_t, ndim=3] out = np.zeros((shape_y,shape_x,3), dtype=np.uint8)
  
  cdef index_t i,j,c
  
  for i in range(shape_y):
    for j in range(shape_x):
      for c in range(3):
        out[i,j,c] = int(255*cmap[gray_in[i,j],c])
        
  return out

        


@cython.boundscheck(False)
@cython.wraparound(False)
cdef _min(float a, float b):
  if a <= b: return a
  else: return b
  
@cython.boundscheck(False)
@cython.wraparound(False)
cdef _max(float a, float b):
  if a >= b: return a
  else: return b
  
@cython.boundscheck(False)
@cython.wraparound(False)
cdef _abs(float a):
  if a < 0: return -1.0*a
  else: return a
  

@cython.boundscheck(False)
@cython.wraparound(False)
cdef _rgb2hsv(float r, float g, float b):
  
  cdef float computedH, computedS ,computedV
  cdef float minRGB, maxRGB, d, h
  
  computedH = 0
  computedS = 0
  computedV = 0

  assert r >= 0 and r <= 255, "Range error, r has to be in range [0,255]"
  assert g >= 0 and g <= 255, "Range error, g has to be in range [0,255]"
  assert b >= 0 and b <= 255, "Range error, b has to be in range [0,255]"

 
  r=r/255.0; g=g/255.0; b=b/255.0
  minRGB = _min(r,_min(g,b))
  maxRGB = _max(r,_max(g,b))

  #Black-gray-white
  if minRGB==maxRGB:
    computedV = minRGB;
    return 0,0,computedV
  

  #Colors other than black-gray-white:
  if r==minRGB:
    d = g-b
  else:
    if b==minRGB:
      d = r-g
    else:
      d = b-r
      
  if r==minRGB:
    h = 3
  else:
    if b==minRGB:
      h = 1
    else:
      h = 5
  
  computedH = 60.0*(h - d/(maxRGB - minRGB))
  computedS = (maxRGB - minRGB)/maxRGB
  computedV = maxRGB
  return computedH,computedS,computedV


@cython.boundscheck(False)
@cython.wraparound(False)
cdef _hsv2rgb(float h, float s, float v):
  
  cdef float chroma, hdash, r, g, b, X, Min
  
  chroma = s*v
  hdash = h/60.0
  X = chroma*(1.0-_abs((hdash%2)-1.0))
  
  if hdash < 1.0:
    r = chroma
    g = X
  elif hdash < 2.0:
    r = X
    g = chroma
  elif hdash < 3.0:
    g = chroma
    b = X
  elif hdash < 4.0:
    g = X
    b = chroma
  elif hdash < 5.0:
    r = X
    b = chroma
  elif hdash < 6.0:
    r = chroma
    b = X
    
  Min = v-chroma
  
  r = r+Min
  g = g+Min
  b = b+Min
  
  return r,g,b


@cython.boundscheck(False)
@cython.wraparound(False)
cpdef _rgbLF2hsvLF(np.ndarray[float_t,ndim=5] lf, np.ndarray[float_t,ndim=5] outLF):
  
  cdef int sv = lf.shape[0]
  cdef int sh = lf.shape[1]
  cdef int sy = lf.shape[2]
  cdef int sx = lf.shape[3]
  
  cdef float _h, _s, _v
  
  assert lf.shape[4] == 3, "Wrong number of channels, can only convert rgb to hsv!"
  
  cdef index_t v,h,y,x
  
  for v in range(sv):
    for h in range(sh):
      for y in range(sy):
        for x in range(sx):
          _h,_s,_v = _rgb2hsv(lf[<unsigned int>v,<unsigned int>h,<unsigned int>y,<unsigned int>x,<unsigned int>0],lf[<unsigned int>v,<unsigned int>h,<unsigned int>y,<unsigned int>x,<unsigned int>1],lf[<unsigned int>v,<unsigned int>h,<unsigned int>y,<unsigned int>x,<unsigned int>2])
          outLF[<unsigned int>v,<unsigned int>h,<unsigned int>y,<unsigned int>x,<unsigned int>0] = _h
          outLF[<unsigned int>v,<unsigned int>h,<unsigned int>y,<unsigned int>x,<unsigned int>1] = _s
          outLF[<unsigned int>v,<unsigned int>h,<unsigned int>y,<unsigned int>x,<unsigned int>2] = _v
          
          
@cython.boundscheck(False)
@cython.wraparound(False)
cpdef _hsvLF2rgbLF(np.ndarray[float_t,ndim=5] lf, np.ndarray[float_t,ndim=5] outLF):
  
  cdef int sv = lf.shape[0]
  cdef int sh = lf.shape[1]
  cdef int sy = lf.shape[2]
  cdef int sx = lf.shape[3]
  
  cdef float _r, _g, _b
  
  assert lf.shape[4] == 3, "Wrong number of channels, can only convert rgb to hsv!"
  
  cdef index_t v,h,y,x
  
  for v in range(sv):
    for h in range(sh):
      for y in range(sy):
        for x in range(sx):
          _r,_g,_b = _hsv2rgb(lf[<unsigned int>v,<unsigned int>h,<unsigned int>y,<unsigned int>x,<unsigned int>0],lf[<unsigned int>v,<unsigned int>h,<unsigned int>y,<unsigned int>x,<unsigned int>1],lf[<unsigned int>v,<unsigned int>h,<unsigned int>y,<unsigned int>x,<unsigned int>2])
          outLF[<unsigned int>v,<unsigned int>h,<unsigned int>y,<unsigned int>x,<unsigned int>0] = _r*255
          outLF[<unsigned int>v,<unsigned int>h,<unsigned int>y,<unsigned int>x,<unsigned int>1] = _g*255
          outLF[<unsigned int>v,<unsigned int>h,<unsigned int>y,<unsigned int>x,<unsigned int>2] = _b*255
          