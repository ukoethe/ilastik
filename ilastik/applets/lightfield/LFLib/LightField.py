from numpy import zeros,copy,uint8,float32,transpose,amin,amax,mean,sqrt
from scipy.ndimage.interpolation import zoom
from sys import exit
from h5py import File
from types import StringType,IntType,ListType,TupleType,FloatType
import pylab as plt
import matplotlib.cm as cm
import traceback
    
    
class LFError(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)

class LazyLF(object):
  
  def __init__(self, h5d):
    self.h5d = h5d
    self.shape = h5d.shape
    self.dtype = h5d.dtype
    
  def __getitem__(self, key):
    if (key == slice(None,None,None)):
      traceback.print_stack()
      print "WARNING: Accessing complete lightfield dataset -> SLOOOOOW !!!!!!!! "
    return self.h5d[key]
    
  def __setitem__(self, key, value):
    self.h5d[key] = value
    

class LightField(object):
  """
  @author: Sven Wanner
  @summary: Base LightField class
  """
  def __init__(self,channels=1, h5f = None):  
    self._h5f = h5f
    self.__type__ = "LightField"
    self.channels = channels #number of color channels
    self.xRes = 0 #data extension in x = shape(LF)[3]
    self.yRes = 0 #data etension in y = shape(LF)[2]
    self.hRes = 1 #angular resolution in horizontal direction
    self.vRes = 1 #angular resolution in vertical direction
    self.dV = 0 #vertical baseline
    self.dH = 0 #horizontal baseline
    self.focalLength = None #camera focal length
    self.camDistance = None #for simulated light field distance to scene center
    self.vSampling = zeros( (1, 1), dtype=float32 ) #relative positions in vertical angular direction
    self.hSampling = zeros( (1, 1), dtype=float32 ) #relative positions in horizontal angular direction
    self.lf = zeros( (1, 1, 1, 1, self.channels), dtype=uint8) #4D raw  data in (v,u,y,x,channels)
    self.depth = None #dataset for depth results
    self.inner = None #used innerScale for depth estimation
    self.outer = None #used outerScale for depth estimation
    self.cvOnly = None #True if only center depth view is stored
    self.tv = None #parameter of tv regularization
    self.gt = None #dataset for ground truth data
    
  def close(self):
    if self._h5f != None:
      self._h5f.close()
    
    
    
def loadLF(fname):
  """
  @author: Sven Wanner
  @summary: loads a LightField from file
  @param fname: <string> filename
  @return: <LF> LightField instance
  """
  if type(fname) == StringType:
    print "\nLoading Light Field:",fname
  else:
    print "Argument Type Error: Cannot handle",type(fname),"in loadLF"
    exit()
  
  try:
    f = File(fname, 'r') 
    LFout = LightField(h5f = f)
  except:  
    raise LFError("HDF5 read/write error")
  try:
    print "try to load light field data ... "
    LFout.lf = LazyLF(f["LF"])
    print "ok"
  except:
    raise LFError("Fatal Error: No LF available!")
  try:
    print "try to load depth data ... ",
    LFout.depth=LazyLF(f["Depth"])
    print "ok"
  except:  
    print "no depth data available"
  try:
    print "try to load ground truth data ... ",
    LFout.gt=LazyLF(f["GT"])
    print "ok"
  except:  
    print "no ground truth data available"


  LFout.xRes = copy(f.attrs["xRes"])
  LFout.yRes = copy(f.attrs["yRes"])
  LFout.vRes = copy(f.attrs["vRes"])
  LFout.hRes = copy(f.attrs["hRes"])
  LFout.dV = copy(f.attrs["dV"])
  LFout.dH = copy(f.attrs["dH"])
  LFout.focalLength = copy(f.attrs["focalLength"])
  LFout.location = fname
  try:
    LFout.camDistance = copy(f.attrs["camDistance"])
  except:
    print "Fatal Error: Old Logfile detected. Add param cam_distance to the LF_Logfile.txt"
    exit()
  try:
    LFout.inner = copy(f.attrs["inner"])
  except:
    LFout.inner = None
  try:
    LFout.outer = copy(f.attrs["outer"])
  except:
    LFout.outer = None
  try:
    LFout.cvOnly = copy(f.attrs["cvOnly"])
  except:
    LFout.cvOnly = None
  try:
    LFout.tv = copy(f.attrs["tv"])
  except:
    LFout.tv = None
  LFout.vSampling = copy(f.attrs["vSampling"])
  LFout.hSampling = copy(f.attrs["hSampling"])
  LFout.channels = copy(f.attrs["channels"])
  
  print "Done"
  return LFout



def saveLF(LFin, outpath=None):
  """
  @author: Sven Wanner
  @summary: saves a LightField 
  @param LFin: <LF> LightField instance
  @param outpath: <string> filename
  """
  
  if outpath is None and LFin.location is not None:
    outpath = LFin.location
  elif outpath is None and LFin.location is None:
    print "Unable to save Lightfield without destination"
    fname = raw_input("Where to store the result? (a) abort")
    if fname == "a":
      import sys
      sys.exit()
    else:
      if fname.find(".h5") == -1:
        fname += ".h5"
      outpath = fname
    return

  try:
    if LFin.__type__ == "LightField":
      pass
  except:
    raise LFError("Argument Error: saveLF can only handle LightField objects!")
    
  try:
    print "\nSaving Light Field:", outpath
    f = File(outpath, 'w')
  except KeyError:
    raise LFError("HDF5 read/write error")
  
  print "write light field"
  f.create_dataset("LF", data=LFin.lf[:], dtype=uint8, compression='gzip', chunks = (1,1,LFin.lf.shape[2],LFin.lf.shape[3],LFin.lf.shape[4]))
  if LFin.depth is not None and len(LFin.depth.shape)==4:
    print "write entire depth estimation"
    f.create_dataset("Depth", data=LFin.depth[:], dtype=float32, compression='gzip', chunks = (1,1,LFin.depth.shape[2],LFin.depth.shape[3]))
  if LFin.depth is not None and len(LFin.depth.shape)==2:
    print "write cv depth estimation"
    f.create_dataset("Depth", data=LFin.depth[:], dtype=float32, compression='gzip', chunks = (LFin.depth.shape[0],LFin.depth.shape[1]))
  if LFin.gt is not None and len(LFin.gt.shape)==4:
    print "write entire ground truth"
    f.create_dataset("GT", data=LFin.gt[:], dtype=float32, compression='gzip', chunks = (1,1,LFin.gt.shape[2],LFin.gt.shape[3]))
  if LFin.gt is not None and len(LFin.gt.shape)==2:
    print "write cv ground truth"
    f.create_dataset("GT", data=LFin.gt[:], dtype=float32, compression='gzip', chunks = (LFin.gt.shape[0],LFin.gt.shape[1]))
  
    
    
  f.attrs["xRes"] = LFin.xRes
  f.attrs["yRes"] = LFin.yRes
  f.attrs["vRes"] = LFin.vRes
  f.attrs["hRes"] = LFin.hRes
  f.attrs["dV"] = LFin.dV
  f.attrs["dH"] = LFin.dH
  f.attrs["focalLength"] = LFin.focalLength
  try:  
    f.attrs["camDistance"] = LFin.camDistance  
  except:
    print "Fatal Error: Old Logfile detected. Add param cam_distance to the LF_Logfile.txt"
    exit()
  if LFin.inner is not None:
    f.attrs["inner"] = LFin.inner
  if LFin.outer is not None:
    f.attrs["outer"] = LFin.outer
  if LFin.cvOnly is not None:
    f.attrs["cvOnly"] = LFin.cvOnly
  if LFin.tv is not None:
    f.attrs["tv"] = LFin.tv
  f.attrs["vSampling"] = LFin.vSampling
  f.attrs["hSampling"] = LFin.hSampling
  f.attrs["channels"] = LFin.channels
  
  f.close()
  print "Done"
  

  
  
def copyLF(LFin):
  """
  @author: Sven Wanner
  @summary: copy a LightField 
  @param LFin: <LF> LightField instance
  @return: <LF> LightField instance
  """
  
  try:
    if LFin.__type__ == "LightField":
      pass
  except:
    raise LFError("Argument Error: saveLF can only handle LightField objects!")
  
  print "\nCopy Light Field"
  lf = LightField()
  lf.xRes = LFin.xRes
  lf.yRes = LFin.yRes
  lf.vRes = LFin.vRes
  lf.hRes = LFin.hRes
  lf.dV = LFin.dV
  lf.dH = LFin.dH
  lf.focalLength = LFin.focalLength  
  try:
    lf.camDistance = LFin.camDistance  
  except:
    print "Fatal Error: Old Logfile detected. Add param cam_distance to the LF_Logfile.txt"
    exit()
  lf.inner = LFin.inner
  lf.outer = LFin.outer
  lf.cvOnly = LFin.cvOnly
  lf.tv = LFin.tv
  lf.vSampling  = LFin.vSampling 
  lf.hSampling  = LFin.hSampling 
  lf.lf = copy(LFin.lf)
  if LFin.depth is not None:
    lf.depth = copy(LFin.depth)
  if LFin.gt is not None:
    lf.gt = copy(LFin.gt)
  if LFin.location is not None:
    lf.location = LFin.location
  lf.channels = LFin.channels
  print "Done"
  
  return lf



def showDepth(lf,view=None,cmap="jet",saveTo=None,show=True):
  
  if cmap=="gray":
    cmap = cm.gray
  elif cmap=="jet":
    cmap=cm.jet
  elif cmap=="hot":
    cmap=cm.hot
  elif cmap=="autumn":
    cmap=cm.autumn
  
  try:
    if lf.__type__ == "LightField":
      pass
  except:
    raise LFError("Argument Error: saveLF can only handle LightField objects!")
  
  if lf.depth is None:
    print "No depth data available"
    return
  
  fig = plt.figure()
  ax = fig.add_subplot(111)
  
  if lf.cvOnly:
    ax.imshow(lf.depth,interpolation='nearest')
  else:
    if view is None:
      view = [lf.vRes/2,lf.hRes/2]
    ax.imshow(lf.depth[view[0],view[1]],interpolation='nearest',cmap=cmap)
  ax.set_xlabel("("+str(amin(lf.depth))+","+str(amax(lf.depth))+") mean="+str(mean(lf.depth)) )
        
    
  if saveTo is not None and type(saveTo) is StringType:
    if saveTo.find(".png") == -1:
      saveTo+=".png"
    print "Save figure to:",saveTo
    plt.savefig(saveTo, transparent = False)
  
  if show: plt.show()
    
  


def showLF(lf,view=None,epi_v=None,epi_h=None,stretch=1,saveTo=None,show=True):
  """
  @author: Sven Wanner
  @summary: simple light field viewer, default show is center view and center epis
  @param lf: LightField instance
  @param view: <int list> view[0] column view[1] row, default:None
  @param view: <int> vertical epi cut column, default:None
  @param view: <int> horizontal epi cut row, default:None
  @param stretch: <float> epi stretch value, default:1
  @param saveTo: <string> save location, if None only show, default:None
  @param show: <bool> show switch, default: True
  """
  try:
    if lf.__type__ == "LightField":
      pass
  except:
    if type(lf)==type("str"):
      try:
        lf=loadLF(lf)
      except:
        raise LFError("Argument Error: no light field found!")
    
  
  if view is None:
    view = [lf.vRes/2,lf.hRes/2]
  if epi_v is None:
    epi_v = lf.xRes/2
  if epi_h is None:
    epi_h = lf.yRes/2
    
  if stretch <= 0:
    stretch = 1
    
  if lf.channels == 3:
    view_im = lf.lf[view[0],view[1],:,:,:]
  else:
    view_im = lf.lf[view[0],view[1],:,:,0]
    
    
  view_im = zeros((lf.yRes,lf.xRes,lf.channels),dtype=uint8)
  for i in range(lf.channels):
    view_im[:,:,i] = lf.lf[view[0],view[1],:,:,i]

    #draw epi markers
    if i==0:
      try:  
        view_im[:,epi_v-1,i] = 200
        view_im[:,epi_v+1,i] = 200
        view_im[epi_h-1,:,i] = 25
        view_im[epi_h+1,:,i] = 25
      except:
        pass
      view_im[:,epi_v,i] = 255
      view_im[epi_h,:,i] = 0
    elif i==1:
      try:
        view_im[epi_h-1,:,i] = 200
        view_im[epi_h+1,:,i] = 200
        view_im[:,epi_v-1,i] = 25
        view_im[:,epi_v+1,i] = 25
      except:
        pass
      view_im[epi_h,:,i] = 255
      view_im[:,epi_v,i] = 0
    else:
      try:
        view_im[:,epi_v+1,i] = 25
        view_im[:,epi_v-1,i] = 25
        view_im[:,epi_v+1,i] = 25
        view_im[:,epi_v-1,i] = 25
      except:
        pass
      view_im[:,epi_v,i] = 0
      view_im[:,epi_v,i] = 0
    
  #extract horizonal epi
  epiH_im = zeros((stretch*lf.hRes,lf.xRes,lf.channels),dtype=uint8)
  for i in range(lf.channels):
    tmp = copy(lf.lf[view[0],:,epi_h,:,i])
    epiH_im[:,:,i] = zoom(tmp,zoom=(stretch,1))
    
  #extract vertical epi 
  epiV_im = zeros((lf.yRes,stretch*lf.vRes,lf.channels),dtype=uint8)
  for i in range(lf.channels):
    tmp = copy(transpose(lf.lf[:,view[1],:,epi_v,i]))
    epiV_im[:,:,i] = zoom(tmp,zoom=(1,stretch))
    
  #fill result image
  img_sy = 1.02*view_im.shape[0]+epiH_im.shape[0]
  img_sx = 1.02*view_im.shape[1]+epiV_im.shape[1]
  img = zeros((img_sy,img_sy,lf.channels),dtype=uint8)
  
  img[0:view_im.shape[0],0:view_im.shape[1],:] = view_im[:]
  img[img.shape[0]-epiH_im.shape[0]-1:-1,0:epiH_im.shape[1],:] = epiH_im[:]
  img[0:epiV_im.shape[0],img.shape[1]-epiV_im.shape[1]-1:-1,:] = epiV_im[:]
  
  #add a border
  gap = int(round(img_sx-view_im.shape[0]-epiH_im.shape[0]))
  result = zeros((img.shape[0]+2*gap,img.shape[1]+2*gap,lf.channels),dtype=uint8)
  
  result[gap:img.shape[0]+gap,gap:img.shape[1]+gap] = img[:]
  
  
  
  #plot
  fig = plt.figure()
  
  ax = fig.add_subplot(111)
  ax.set_title("view: [v,h] = ["+str(view[0])+","+str(view[1])+"] epi_v at x ="+str(epi_v)+" epi_h at y ="+str(epi_h))

  if lf.channels == 1:
    result = result[:,:,0]
  ax.imshow(result,interpolation='nearest')
  
  if saveTo is not None and type(saveTo) is StringType:
    if saveTo.find(".png") == -1:
      saveTo+=".png"
    print "Save figure to:",saveTo
    plt.savefig(saveTo, transparent = False)
  
  if show: plt.show()
  
  
  
  
def refocusLF(lf,shifts=None):
  """
  @author: Sven Wanner
  @summary: refocus a light field 
  @param lf: LightField instance
  @param shifts: <float/2d list of floats> shift values, default: None
  @return: LightField instance
  """
  from scipy.ndimage import shift
  print "\nShift LightField"
  outLF = copyLF(lf)
  
  if shifts is None or shifts==0:
    print "Warning, no shift given, non refocused light field is returned"
    return outLF
  
  if type(shifts) == type(1.0) or type(shifts) == type(1):
    shifts = (shifts,shifts)
  
  if type(shifts) == type([]) or type(shifts) == type(()):
    for v in range(lf.vRes):
      for h in range(lf.hRes):
        
        #calc normed img position vector
        imPos = [lf.vSampling[v,h]/lf.dV,lf.hSampling[v,h]/lf.dH]
        print imPos
        
        shiftVals = [shifts[0]*imPos[0],shifts[1]*imPos[1]]
        
        for c in range(lf.channels):
          outLF.lf[v,h,:,:,c] = shift(lf.lf[v,h,:,:,c],shiftVals)
        
  else:
    print "Warning, shift type error, non refocused light field is returned"
  
  return outLF



def denoiseDepth(lf,weight,iter):
  from LFLib.ImageProcessing.filter import tv_regularizer
  
  for i in range(lf.vRes):
    for j in range(lf.hRes):
      for c in range(3):
        lf.depth[i,j,:,:] = tv_regularizer(lf.depth[i,j,:,:],weight,iter)
        
  return lf
  
  