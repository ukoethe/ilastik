import types
import numpy as np

from  utils import colorRange

import libfilter as fast



def anisotropicDiffusion(im,iteration,kappa,delta_t):
  """
  anisotropic diffusion based on malik
  """
  return fast._anisotropicDiffusion(im,iteration,kappa,delta_t)



  
 
    
def tv_regularizer(im, weight=0.5, n_iter_max=200, p=1):
  """
  tv regularizing
  """
  cannels = 0  
  
  im = im.astype(np.float32)
  
  if len(im.shape)==2:
    tmp = np.zeros((im.shape[0],im.shape[1],1),dtype=np.float32)
    tmp[:,:,0] = im[:]
    im = np.copy(tmp)
    channels = 1
    
  if len(im.shape)==3:
    channels = im.shape[2]
    u = np.zeros((im.shape[0],im.shape[1],channels),dtype=np.float32)
    old_Range = []
  
    for i in range(channels):
      old_Range.append([np.amin(im[:,:,i]),np.amax(im[:,:,i])])
      
    
    for channel in range(channels):
      if type(weight) is types.IntType or type(weight) is types.FloatType:
      
        xi_x = np.zeros_like(im[:,:,channel]).astype(np.float32)
        xi_y = np.zeros_like(im[:,:,channel]).astype(np.float32)
        q = np.zeros_like(im[:,:,channel]).astype(np.float32)
        
        lamda = weight
        
        tau = 1.0/np.sqrt(8.0)
        
        u[:,:,channel] = np.copy(im[:,:,channel]).astype(np.float32)
        
        i=0
        while i < n_iter_max:
          gy,gx = fast._grad(u[:,:,channel])
          xi_y += tau*gy
          xi_x += tau*gx
          xi_y,xi_x = fast._normP(xi_y,xi_x)
          
          q = q[:] + tau*(u[:,:,channel]-im[:,:,channel])
          q = fast._normQ(q.astype(np.float32),lamda,tau,p)

          div = fast._div(xi_y,xi_x)
          u[:,:,channel] = u[:,:,channel] + tau*(div[:] - q[:])
          
          u[:,:,channel] = colorRange(u[:,:,channel],old_Range[channel])
      
          i+=1      
    if channels == 1:
      return u[:,:,0]
    else:
      return u
  
  else:
    print "ERROR: tv_weightDenoise need scalar weight!"
    return None





def tv_weightDenoise(im, weight=None, n_iter_max=100, lamda=1):
  """
  tv denoising using a weighted reprojection
  """
  if len(im.shape)!=2:
    print "ERROR: tv_weightDenoise needs 2d image array!"
    return None
    
  xi_x = np.zeros_like(im)
  xi_y = np.zeros_like(im)
  
  if (str(type(weight)) == "<type 'numpy.ndarray'>") and (len(weight.shape)==2):
    if np.amax(weight) > 1 or np.amin(weight) < 0:
      print "WARNING: tv_weightDenoise arg weight was rescaled  ->  [0,1]"
      weight = colorRange(weight,newRange=[0,1])
  else:
    print "WARNING: tv_weightDenoise need 2d ndarray as weight! weight is set to np.ones!"
    weight = np.zeros_like(im)
    weight[:,:] = 1
 
  tau = 1.0/(4.0*lamda+1e-3)
  
  u = np.copy(im)
  
  i=0
  while i < n_iter_max:

    div = fast._div(xi_y,xi_x)
    u = u - lamda * div
    gy,gx = fast._grad(u)
    xi_y -= tau*gy
    xi_x -= tau*gx
    xi_y,xi_x = fast._weightNormP(weight,xi_y,xi_x)
    i+=1
  
  return u



