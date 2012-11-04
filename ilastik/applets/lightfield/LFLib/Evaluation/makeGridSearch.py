import sys
import numpy as np
from LFLib.LightField import saveLF,loadLF
from LFLib.ImageProcessing.ui import gridPlot
from LFLib.LFDepth.depth import calcDepth
from LFLib.Blender import disparityToDepth, depthToDisparity

from LFLib.settings import *


def gridSearch(lf,stepSize,save=None,title=""):
  
  #prepare gridsearch, search range intervals and create grid
  rangeLookup = {"5":1.3,"7":1.5,"9":1.9,"11":2.0,"13":2.1,"15":2.2,"17":2.3}
  
  minRes = lf.vRes
  if lf.hRes<lf.vRes:
    minRes = lf.hRes
    
  iorange = [0.7,rangeLookup[str(minRes)]]
    
  steps = int(np.round(((iorange[1]-iorange[0])/stepSize)+1))
  stop = iorange[0]+steps*stepSize
  innerRange = np.arange(iorange[0],stop,stepSize)
  
  steps = int(np.round(((iorange[1]-iorange[0])/stepSize)+1))
  stop = iorange[0]+steps*stepSize
  outerRange = np.arange(iorange[0],stop,stepSize)
  
  grid = np.zeros((innerRange.shape[0],outerRange.shape[0]))
  
  
  
  #do gridsearch
  for m,inner in enumerate(innerRange):
    for n,outer in enumerate(outerRange):
      
      try:
        calcDepth(lf,inner,outer)
      except:
        return
      
      d = disparityToDepth(lf.depth,lf.dH,lf.camDistance,lf.focalLength,lf.xRes)
      
      diff = np.abs(d[:]-lf.gt[:])/lf.gt[:]
      error = len(np.where(diff<0.005)[0])
      
      print "found error for inner",inner," outer",outer," error:",error
      
      grid[m,n] = error


  del lf
  
  if save is not None:
    fname = save+"_inner.npy"
    np.save(fname, innerRange)
    fname = save+"_outer.npy"
    np.save(fname, outerRange)
    fname = save+"_grid.npy"
    np.save(fname, grid)
  
  try:
    gridPlot(outerRange,innerRange,grid,save=save,title=title)
  except:
    return

  argmax = np.where(grid==np.amax(grid))
  optInner = float(innerRange[argmax[0][0]])
  optOuter = float(outerRange[argmax[1][0]]) 
  
  return optInner,optOuter











##########################################################################################
#
#                                        U S A G E 
#
##########################################################################################

def makeGridSearch(datakey,typekey=None,reskey=None,stepSize=0.1,title="Grid Search",saveloc="/tmp/gplot"):
  try:
    if typekey is not None and reskey is not None:
      fname = lfs[datakey][typekey][reskey]
    elif reskey is not None:
      fname = lfs[datakey][reskey]
    else:
      fname = lfs[datakey]
  except:
    print "Key Error..."
    return
    
  save = saveloc
  
  try:
    lf = loadLF(fname)
  except:
    return
  
  try:
    optInner,optOuter = gridSearch(lf,stepSize,save=save,title=title)
    calcDepth(lf,optInner,optOuter)
    saveLF(lf)
  except:
    return
  
  

if __name__ == "__main__":
  
  
  stepSize = 0.1
  save = None
  title = "Grid Search"
  
  if len(sys.argv) == 1:
    fname = lfs["buddha"]["clean"]["5x5"]
  elif len(sys.argv) == 2:
    fname = sys.argv[1]
  elif len(sys.argv) == 3:
    fname = sys.argv[1]
    save = sys.argv[2]
  elif len(sys.argv) == 4:
    fname = sys.argv[1]
    save = sys.argv[2]
    title = sys.argv[3]
  else:
    print "arg1: filename\narg2: save location\narg3: title"
    sys.exit()
    
  lf = loadLF(fname)
  
  optInner,optOuter = gridSearch(lf,stepSize,save=save,title=title)
  
  calcDepth(lf,optInner,optOuter)
  saveLF(lf)