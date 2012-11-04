import numpy as np
from sys import exit
import types


def drawLabeledLayers(img,layer):
  
  if type(layer) is not types.ListType:
    layer = [layer]
  
  out = np.zeros((img.shape[0],img.shape[1],3),dtype=np.float32)
  colors = [(255,0,0),(0,255,0),(0,0,255),(255,200,0),(200,255,0),(0,200,255),(0,255,200)]
  
  for i in range(3):
    if len(img.shape)==2:
      out[:,:,i] = img[:,:]
    elif len(img.shape)==3 and img.shape[2] == 3:
      out[:,:,i] = img[:,:,i]
    else:
      print "Error, image type not supported!"
      exit()

  for i in range(len(layer)):
    assert img.shape[0] == layer[i].shape[0], "image and layer hasn't the same size"
    assert img.shape[1] == layer[i].shape[1], "image and layer hasn't the same size"
    
    try:
      positions = np.where(layer[i]!=0)
      label = layer[i][positions[0][0],positions[1][0]]
      if i > 6:
        colors.append((np.random.randint(0,255,1)[0],np.random.randint(0,255,1)[0],np.random.randint(0,255,1)[0]))
      out[positions] = colors[i]
    except Exception as e:
      print e
      print "Warning in drawLabeledLayers, maybe layer is empty!"

  
  return out
        
  
  
  
  
  
  
  
    