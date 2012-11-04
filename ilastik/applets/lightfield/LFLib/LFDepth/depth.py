import numpy as np
from LFLib.LFDepth.depthFromStructureTensor import *
from types import StringType, ListType, TupleType
from LFLib.ImageProcessing.ui import show
from LFLib.ImageProcessing.filter import tv_regularizer
from LFLib.Blender import depthToDisparity
from LFLib.LightField import refocusLF





def calcDepth(lf,inner=0.6,outer=0.8,sigmaXStrength=1.0,maxLabel=4,minLabel=-4,cohSmooth=0.8,colorMode=0,tv=None,roi=None,full=False,useThreading=True):
  """
  @author: Sven Wanner
  @brief: calculates a depth field from the input light field instance
  @param lf: <object> LightField instance
  @param inner: <float> inner scale of structure tensor, default:0.6
  @param outer: <float> outer scale of structure tensor, default:0.8
  @param sigmaXStrength: <float> factor of inner scale x smoothing amount innerScale=(inner,inner*sigmaXStrength), default:1.0
  @param maxLabel: <float> maximum label threshold, default:3
  @param minLabel: <float> minimum label threshold, default:-3
  @param cohSmooth: <float> sigma of the coherence smoothing, default:0.8
  @param colorMode: <int> rgb conversion parameter, 0-> to gray, 1 to value from hsv, default: 0
  @param tv: <dict> if not None tv denoising is applied, tv[lambda]=lambda, tv[iter]=iterations, tv[type]=Normtype 1 o 2, default: None
  @param roi: <2x2 int list> [[fromY,toY],[fromX,toX]] default:None
  @param full: <bool> full depth storage, default:False
  """
  
  
  if lf.gt is not None:
    gt = depthToDisparity(lf.gt,lf.dH,lf.camDistance,lf.focalLength,lf.xRes)
  
  if colorMode != 0 or colorMode != 1:
    colorMode = 0
  
  print "\nDepth estimation using paramteter:"
  print "innerScale:",inner
  print "outerScale:",outer
  print "sigmaXStrength:",sigmaXStrength
  print "maxLabel:",maxLabel
  print "minLabel",minLabel
  print "cohSmooth",cohSmooth
  print "colorMode",colorMode
  print "roi:",roi
  print "full:",full  
  print "useThreading",useThreading
  print "....................................."
  
  
  DST = DepthFromStructureTensor()
  DST.inputLF.setValue(lf.lf)
  DST.innerScale.setValue(inner)
  DST.outerScale.setValue(outer)
  DST.sigmaXStrength.setValue(sigmaXStrength)
  DST.maxLabel.setValue(maxLabel)
  DST.minLabel.setValue(minLabel)
  DST.colorMode.setValue(colorMode)
  DST.coherenceSmooth.setValue(cohSmooth)
  DST.useThreading.setValue(useThreading)
  
  if roi is None:
    dest = DST.outputLF[:].allocate().wait()
  else:
    dest = DST.outputLF[:,:,roi[0][0]:roi[0][1],roi[1][0]:roi[1][1],:].allocate().wait()

  if full:
    lf.cvOnly = False
    if tv is not None:
      if type(tv) == type({}) and len(tv) == 3:
        for i in range(dest.shape[0]):
          for j in range(dest.shape[1]):
            dest[i,j,:,:,0] = tv_regularizer(dest[i,j,:,:,0],tv["lambda"],tv["iter"],tv["type"])
      else:
        print "Warning, error in tv regularizing parameter, a non smoothed result is returned!"
    lf.depth = dest[:,:,:,:,0]
  else:    
    lf.cvOnly = True
    view = [lf.vRes/2,lf.hRes/2]
    if tv is not None:
      if type(tv) == type({}) and len(tv) == 3:
        dest[view[0],view[1],:,:,0] = tv_regularizer(dest[view[0],view[1],:,:,0],tv["lambda"],tv["iter"],tv["type"])
      else:
        print "Warning, error in tv regularizing parameter, a non smoothed result is returned!"
    lf.depth = dest[view[0],view[1],:,:,0]
    
  lf.inner = inner
  lf.outer = outer
  if tv is not None:
    lf.tv = np.array(tv)
  
  

        
        
        
        