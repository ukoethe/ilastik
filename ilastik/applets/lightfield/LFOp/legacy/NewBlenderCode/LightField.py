from numpy import zeros,copy,uint8,float32
from sys import exit
from h5py import File
from types import StringType


    
    
class LFError(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)
    
    

class LightField(object):
  """
  @author: Sven Wanner
  @summary: Base LightField class
  """
  def __init__(self,channels=1):  
    
    self.__type__ = "LightField"
    self.channel = channels #number of color channels
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
    self.lf = zeros( (1, 1, 1, 1, self.channel), dtype=uint8) #4D raw  data in (v,u,y,x,channels)
    self.depth = None #dataset for depth results
    self.gt = None #dataset for ground truth data
    
    
    
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
    LFout = LightField()
    f = File(fname, 'r') 
  except:  
    raise LFError("HDF5 read/write error")
  try:
    LFout.lf = copy(f["LF"])
  except:
    raise LFError("Fatal Error: No LF available!")
  try:
    LFout.depth=copy(f["Depth"])
  except:  
    print "No depth data available"
  try:
    LFout.gt=copy(f["GT"])
  except:  
    print "No ground truth data available"


  LFout.xRes = copy(f.attrs["xRes"])
  LFout.yRes = copy(f.attrs["yRes"])
  LFout.vRes = copy(f.attrs["vRes"])
  LFout.hRes = copy(f.attrs["hRes"])
  LFout.dV = copy(f.attrs["dV"])
  LFout.dH = copy(f.attrs["dH"])
  LFout.focalLength = copy(f.attrs["focalLength"])
  LFout.camDistance = copy(f.attrs["camDistance"])
  LFout.vSampling = copy(f.attrs["vSampling"])
  LFout.hSampling = copy(f.attrs["hSampling"])
  LFout.channel = copy(f.attrs["channels"])

  f.close()
  
  print "Done"
  return LFout



def saveLF(LFin, outpath):
  """
  @author: Sven Wanner
  @summary: saves a LightField 
  @param LFin: <LF> LightField instance
  @param outpath: <string> filename
  """
  
  if str(type(LFin)) != "<class 'LightField.LightField'>":
    raise LFError("Argument Error: saveLF can only handle LightField objects!")
  try:
    print "\nSaving Light Field:", outpath
    f = File(outpath, 'w')
  except KeyError:
    raise LFError("HDF5 read/write error")
    
  f.create_dataset("LF", data=LFin.lf, dtype=uint8, compression='gzip')
  if LFin.depth is not None:
    f.create_dataset("Depth", data=LFin.depth, dtype=float32, compression='gzip')
  if LFin.gt is not None:
    f.create_dataset("GT", data=LFin.gt, dtype=float32, compression='gzip')
  f.attrs["xRes"] = LFin.xRes
  f.attrs["yRes"] = LFin.yRes
  f.attrs["vRes"] = LFin.vRes
  f.attrs["hRes"] = LFin.hRes
  f.attrs["dV"] = LFin.dV
  f.attrs["dH"] = LFin.dH
  f.attrs["focalLength"] = LFin.focalLength  
  f.attrs["camDistance"] = LFin.camDistance  
  f.attrs["vSampling"] = LFin.vSampling
  f.attrs["hSampling"] = LFin.hSampling
  f.attrs["channels"] = LFin.channel
  
  f.close()
  print "Done"
  
  
  
def copyLF(LFin):
  """
  @author: Sven Wanner
  @summary: copy a LightField 
  @param LFin: <LF> LightField instance
  @return: <LF> LightField instance
  """
  
  if str(type(LFin)) != "<class 'LightField.LightField'>":
    raise LFError("Argument Error: copyLF can only handle LightField objects!")
    
  print "\nCopy Light Field"
  lf = LightField()
  lf.xRes = LFin.xRes
  lf.yRes = LFin.yRes
  lf.vRes = LFin.vRes
  lf.hRes = LFin.hRes
  lf.dV = LFin.dV
  lf.dH = LFin.dH
  lf.focalLength = LFin.focalLength  
  lf.camDistance = LFin.camDistance  
  lf.vSampling  = LFin.vSampling 
  lf.hSampling  = LFin.hSampling 
  lf.lf = copy(LFin.lf)
  if LFin.depth is not None:
    lf.depth = copy(LFin.depth)
  if LFin.gt is not None:
    lf.gt = copy(LFin.gt)
  lf.channel = LFin.channel
  print "Done"
  
  return lf
