import numpy as np


def colorRange(arr,newRange=[0,255]):
  """
   @brief: adjust the value range of a ndarray to the newRange
   @param arr: <ndarray> input array
   @param newRange: <int list> new color range
   @return: <ndarray>
   """
  amin = np.amin(arr)
  amax = np.amax(arr)
  if amin == amax:
    return arr
  else:
    oldRange = [amin,amax]
    oldDiff = oldRange[1] - oldRange[0]
    newDiff = newRange[1] - newRange[0]
    out = (arr - oldRange[0]) / oldDiff * newDiff + newRange[0]
    return out
    
    
def mfig2ndarray(fig):
   """
   @brief: Convert a Matplotlib figure to a 4D numpy array with RGBA channels and return it
   @param fig: a matplotlib figure
   @return: <ndarray> a numpy 3D array of RGBA values
   """
   # draw the renderer
   fig.canvas.draw ( )

   # Get the RGBA buffer from the figure
   w,h = fig.canvas.get_width_height()
   buf = np.fromstring ( fig.canvas.tostring_argb(), dtype=np.uint8 )
   buf.shape = ( w, h,4 )

   # canvas.tostring_argb give pixmap in ARGB mode. Roll the ALPHA channel to have it in RGBA mode
   buf = np.roll ( buf, 3, axis = 2 )
   return buf