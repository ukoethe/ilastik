import numpy as np
import h5py as h5
import types
import glob
import OpenEXR, Imath


from LF.Utils import utils as util
import vigra

#import pyximport; pyximport.install()
#import fast
import LF.lib.fast_base as fast

class LFError(Exception):
  def __init__(self, value):
    self.value = value
  def __str__(self):
    return repr(self.value)
  

class LightField:

  def __init__(self,channels=1,dtype="uint8"):
    """
    LF Structure: x = cam positions   
     
                          horizontal EPI        vertical EPI
                          LF[v,:,y,:,:]         LF[:,h,:,x,:]          
                          
                                                      |
        x   x   x         x   x   x               x   x   x  
                                                      |
        x   x   x      ---x---x---x--- v          x   x   x  
                                                      |      
        x   x   x         x   x   x               x   x   x
                                                      |
                                                      h                    
    """     
    
    self.dtype = dtype
    self.channel = channels
    self.xRes = 0      #data extension in x = np.shape(LF)[3]
    self.yRes = 0      #data etension in y = np.shape(LF)[2]
    self.hRes = 1    #angular resolution in horizontal direction
    self.vRes = 1    #angular resolution in vertical direction
    self.dH = 1           #step width in horizontal direction
    self.dV = 1           #step width in vertical direction
    self.vSampling = np.zeros( (1, 1), dtype=np.float32 ) #relative positions in vertical angular direction
    self.hSampling = np.zeros( (1, 1), dtype=np.float32 ) #relative positions in horizontal angular direction
    self.LF = np.zeros( (1, 1, 1, 1, self.channel), dtype=self.dtype ) #raw 4D data in (v,u,y,x,channels)
    
    
    
def loadLF(infile,debug=0):
  if type(infile) == types.StringType:
    print "try to load:",infile
  #try:
  LFout = LightField()
  f = h5.File(infile, 'r') 
  try:
    LFout.LF=np.copy(f["LF"])
  except:
    try:
      LFout.LF=np.copy(f["Depth"])
    except:  
      raise LFError("HDF5 read/write error")

  #print list(f.attrs)
  LFout.xRes = np.copy(f.attrs["xRes"])
  LFout.yRes = np.copy(f.attrs["yRes"])
  LFout.vRes = np.copy(f.attrs["vRes"])
  LFout.hRes = np.copy(f.attrs["hRes"])
  LFout.dV = np.copy(f.attrs["dV"])
  LFout.dH = np.copy(f.attrs["dH"])
  LFout.vSampling = np.copy(f.attrs["vSampling"])
  LFout.hSampling = np.copy(f.attrs["hSampling"])
  LFout.dtype = np.copy(f.attrs["dtype"])
  LFout.channel = np.copy(f.attrs["channels"])
  
  if debug:
    print "\n######## load light field ##########"
    print "properties:"
    print "xRes =", np.copy(f.attrs["xRes"])
    print "yRes =", np.copy(f.attrs["yRes"])
    print "vRes =", np.copy(f.attrs["vRes"])
    print "hRes =", np.copy(f.attrs["hRes"])
    print "dV =", np.copy(f.attrs["dV"])
    print "dH =", np.copy(f.attrs["dH"])
    print "vSampling =", np.copy(f.attrs["vSampling"])
    print "hSampling =", np.copy(f.attrs["hSampling"])
    if np.copy(f.attrs["dV"]) != 0:
      print "vPositions =", np.copy(f.attrs["vSampling"])/np.copy(f.attrs["dV"])
    if np.copy(f.attrs["dH"]) != 0:
      print "hPositions =", np.copy(f.attrs["hSampling"])/np.copy(f.attrs["dH"])
    print "dtype =", np.copy(f.attrs["dtype"])
    print "channels =", np.copy(f.attrs["channels"])
    print "######################################\n"
  
  f.close()
  return LFout
  #except KeyError:
  #  raise LFError("HDF5 read/write error")
  
    
    
def saveLF(LFin, outpath):
  try:
    print "saving", outpath
    f = h5.File(outpath, 'w')
    if LFin.dtype == "float32":
      f.create_dataset("Depth", data=LFin.LF, dtype=LFin.dtype, compression='gzip')
    else:
      f.create_dataset("LF", data=LFin.LF, dtype=LFin.dtype, compression='gzip')
    f.attrs["xRes"] = LFin.xRes
    f.attrs["yRes"] = LFin.yRes
    f.attrs["vRes"] = LFin.vRes
    f.attrs["hRes"] = LFin.hRes
    f.attrs["dV"] = LFin.dV
    f.attrs["dH"] = LFin.dH
    f.attrs["vSampling"] = LFin.vSampling
    f.attrs["hSampling"] = LFin.hSampling
    f.attrs["dtype"] = LFin.dtype
    f.attrs["channels"] = LFin.channel
    
    f.close()
    print "done"
  except KeyError:
    raise LFError("HDF5 read/write error")
  
  
def copyLF(LFin):
  lf = LightField()
  lf.xRes = LFin.xRes
  lf.yRes = LFin.yRes
  lf.vRes = LFin.vRes
  lf.hRes = LFin.hRes
  lf.dV = LFin.dV
  lf.dH = LFin.dH
  lf.vSampling  = LFin.vSampling 
  lf.hSampling  = LFin.hSampling 
  lf.LF = np.copy(LFin.LF)
  lf.dtype = LFin.dtype
  lf.channel = lf.channel
  
  return lf
  
  
def copyDefaultLF(LFarray):
  lf = LightField()
  lf.xRes = LFarray.shape[3]
  lf.yRes = LFarray.shape[2]
  lf.vRes = LFarray.shape[0]
  lf.hRes = LFarray.shape[1]
  lf.dV = 1
  lf.dH = 1
  lf.vSampling  = LFin.vSampling 
  lf.hSampling  = LFin.hSampling 

  if len(LFarray.shape)==5:  
    lf.LF = LFarray
  else:
    lf.LF = np.zeros((LFarray.shape[0],LFarray.shape[1],LFarray.shape[2],LFarray.shape[3],1),dtype=LFarray.dtype)
    lf.LF[:,:,:,:,0] = LFarray[:,:,:,:]
  lf.dtype = LFarray.dtype
  if len(LFarray.shape)==5:
    lf.channel = LFarray.shape[4]
  else:
    lf.channel = 1
  
  return lf



def fromBlender(path, creation_type, channels=1, outname="", outpath=None ,disparity=True):
  """
  arg1 path : location of Logfile.txt
  arg2 type : "l"->only lightfield, "d"->only depth for center view, "a"->lightfield and depth for center view, "fd"->lightfield and full groundtruth field
  """

  
  if outpath is None:
    outpath = path
    
    
  lfile = open(path+"/LF_logfile.txt")
  space_range = [0,0]
  steps = [0,0]
  center_view = 0
  cam_rotation = None
  cam_shifts = None
  cam_positions = None
  resolution = None
  focal_length_rad = 0
  
  while 1:
    line = lfile.readline()
    if not line:
        break
    
    if line.find("space_range_x") != -1:
      space_range[1] = float(line[line.find(":")+1:])
    if line.find("space_range_y") != -1:
      space_range[0] = float(line[line.find(":")+1:])
    if line.find("steps_x") != -1:
      steps[1] = int(line[line.find(":")+1:])
    if line.find("steps_y") != -1:
      steps[0] = int(line[line.find(":")+1:])
    if line.find("cam rotation") != -1:
      arr_str = line[line.find(":")+1:]
      arr_str = arr_str.replace("\n","")
      cam_rotation = util.toList(arr_str)
    if line.find("cam_shifts") != -1:
      arr_str = line[line.find(":")+1:]
      arr_str = arr_str.replace("\n","")
      cam_shifts = util.o2ListToList(arr_str)
    if line.find("positions") != -1:
      arr_str = line[line.find(":")+1:]
      arr_str = arr_str.replace("\n","")
      cam_positions = util.o2ListToList(arr_str)
    if line.find("scene_dimensions") != -1:
      arr_str = line[line.find(":")+1:]
      arr_str = arr_str.replace("\n","")
      scene_dimensions = util.toList(arr_str)
    if line.find("scene_center") != -1:
      arr_str = line[line.find(":")+1:]
      arr_str = arr_str.replace("\n","")
      scene_center = util.toList(arr_str)
    if line.find("focal_length [rad]") != -1:
      focal_length_rad = float(line[line.find(":")+1:])
    if line.find("resolution") != -1:
      arr_str = line[line.find(":")+1:]
      arr_str = arr_str.replace("\n","")
      resolution = util.toList(arr_str)
    if line.find("cam_matrix_ext") != -1:
      arr_str = line[line.find(":")+1:]
      arr_str = arr_str.replace("\n","")
      cam_matrix_ext = util.o3ListToList(arr_str)
    if line.find("cam_matrix_int") != -1:
      arr_str = line[line.find(":")+1:]
      arr_str = arr_str.replace("\n","")
      cam_matrix_int = util.o3ListToList(arr_str)
  
  center_view = steps[0]*(2*steps[1]+1)+steps[1]
  
  params = {"space_range":space_range,
            "steps":steps,
            "center_view":center_view,
            "focal_length_rad":focal_length_rad,
            "scene_dimensions":scene_dimensions,
            "scene_center":scene_center,
            "resolution":resolution,
            "cam_rotation":cam_rotation,
            "cam_shifts":cam_shifts,
            "cam_positions":cam_positions,
            "cam_matrix_int":cam_matrix_int,
            "cam_matrix_ext":cam_matrix_ext
  }
  
  if creation_type == "l" or creation_type == "a" or creation_type == "fd":
    lf = make_LF_fromBlender(path+"/images/",params,channels=channels)
    if channels == 3:
      name = "/lf_"+outname+"_"+str(steps[0]*2+1)+"x"+str(steps[1]*2+1)+"_rgb.lf"
    else:
      name = "/lf_"+outname+"_"+str(steps[0]*2+1)+"x"+str(steps[1]*2+1)+".lf"
    
    saveLF(lf,outpath+name)
  if creation_type == "d" or creation_type == "a":
    
    depth_path = ""

    for f in glob.glob(path+"/depth/*.exr"):
        a = f[f.find("depth/")+6:]
        if int(a[a.find("_")-3:a.find("_")]) == center_view:
            depth_path = f
            
    
    pt = Imath.PixelType(Imath.PixelType.FLOAT)
    golden = OpenEXR.InputFile(depth_path)
    dw = golden.header()['dataWindow']
    size = (dw.max.x - dw.min.x + 1, dw.max.y - dw.min.y + 1)
    depthstr = golden.channel('R', pt)
    depth = np.fromstring(depthstr, dtype = np.float32)
    depth.shape = size
  
    name = "/depth_"+str(steps[0]*2+1)+"x"+str(steps[1]*2+1)+".npy"
    
    np.save(outpath+name,depth)
    
  if creation_type == "fd":
    depths = []
    paths = []
    for f in glob.glob(path+"/depth/*.exr"):
      paths.append(f)
    paths.sort()
    for f in paths:
      pt = Imath.PixelType(Imath.PixelType.FLOAT)
      golden = OpenEXR.InputFile(f)
      dw = golden.header()['dataWindow']
      size = (dw.max.x - dw.min.x + 1, dw.max.y - dw.min.y + 1)
      depthstr = golden.channel('R', pt)
      depth = np.fromstring(depthstr, dtype = np.float32)
      depth.shape = size
      depths.append(depth)
      
    length = len(depths)
    out = np.zeros((length,depths[0].shape[0],depths[0].shape[1]),dtype=np.float32)
    for i in range(length):
      out[i,:,:] = depths[i][:,:]
      
    lf = make_LF_fromBlender(out,params,"depth",disparity)
    
    name = "/lf_groundtruth_"+outname+"_"+str(steps[0]*2+1)+"x"+str(steps[1]*2+1)+".h5"

    saveLF(lf,outpath+name)



def make_LF_fromBlender(filepath,params,flag=None,disparity=True,channels=1):

  images=[]
  
  if type(filepath) == types.StringType:
    #read filenames and sort
    files = []
    try:
      for f in glob.glob(filepath+"*.png"):
        files.append(f)
      files.sort()
    except:
      print "Files not found"
      return None
    
    
  
    #read images and convert to gray scale
    for f in files:
      
      im = np.transpose(vigra.readImage(f).view(np.ndarray))
      if channels == 1:
        im = 0.3*im[0,:,:]+0.59*im[1,:,:]+0.11*im[2,:,:]
      else:
        im = im[0:3,:,:]
      images.append(im)
      
  elif str(type(filepath)) == "<type 'numpy.ndarray'>":
    for i in range(filepath.shape[0]):
      images.append(filepath[i,:,:])
      

  #stack LF array
  lf = LightField()
  lf.channel = channels

  steps = params["steps"]
  if channels == 1 or flag == "depth":
    shape = [float(images[0].shape[0]),float(images[0].shape[1])]
  else:
    shape = [float(images[0].shape[1]),float(images[0].shape[2])]
  if flag == "depth":
    lf_array = np.zeros((2*steps[0]+1,2*steps[1]+1,shape[0],shape[1],1),np.float32)
  else:
    lf_array = np.zeros((2*steps[0]+1,2*steps[1]+1,shape[0],shape[1],channels),np.uint8)
    
  lf_camRotation = np.array([0,0,0],dtype=np.float32)
  lf_sceneDimensions = np.array([0,0,0],dtype=np.float32)
  lf_sceneCenter = np.array([0,0,0],dtype=np.float32)
  lf_camShifts = np.zeros((2*steps[0]+1,2*steps[1]+1,2),dtype=np.float32)
  lf_camPositions = np.zeros((2*steps[0]+1,2*steps[1]+1,3),dtype=np.float32)
  lf_intMatrices = np.zeros((2*steps[0]+1,2*steps[1]+1,3,3),dtype=np.float32)
  lf_extMatrices = np.zeros((2*steps[0]+1,2*steps[1]+1,4,4),dtype=np.float32)
  
  for i in range(3):
    lf_camRotation[i] = params["cam_rotation"][i]
    lf_sceneDimensions[i] = params["scene_dimensions"][i]
    lf_sceneCenter[i] = params["scene_center"][i]

  
  n=0
  for i in range(2*steps[0]+1):
    for j in range(2*steps[1]+1):
      
      if flag == "depth":
        lf_array[i,j,:,:,0] = np.copy(images[0][:,:])
        
      else:
        for c in range(channels):
          if channels == 1:
            lf_array[i,j,:,:,c] = np.copy(images[0][:,:])
          else:
            lf_array[i,j,:,:,c] = np.copy(images[0][c,:,:])
      
      images.pop(0)
        
      for k in range(3):
        
        if k<2:
          lf_camShifts[i,j,k] = params["cam_shifts"][n][k]
          lf_camPositions[i,j,k] = params["cam_positions"][n][k]
        else: lf_camPositions[i,j,k] = params["cam_positions"][n][k]
      for k in range(3):
        for l in range(3):
          lf_intMatrices[i,j,k,l] = params["cam_matrix_int"][n][k][l]
      for k in range(4):
        for l in range(4):
          lf_extMatrices[i,j,k,l] = params["cam_matrix_ext"][n][k][l]
      n+=1
      
  if flag == "depth" and disparity:
    lf_array = depthToDisparity(lf_array,lf_camShifts,lf_intMatrices,lf_extMatrices,lf_camPositions,params["focal_length_rad"],params["space_range"][0]/steps[1])
    lf.dtype = 'float32'
    
  lf.LF = lf_array

  lf.yRes = lf.LF[0,0,:,:,0].shape[0]
  lf.xRes = lf.LF[0,0,:,:,0].shape[1]
  lf.vRes = lf.LF.shape[0]
  lf.hRes = lf.LF.shape[1]

  pilot_h = np.arange(-steps[1],steps[1]+1,dtype=np.float32)
  pilot_v = np.arange(-steps[0],steps[0]+1,dtype=np.float32)
  
  if steps[1] != 0:
    dH = params["space_range"][1]/float(steps[1])
  else: dH = 0
  if steps[0] != 0:
    dV = params["space_range"][0]/float(steps[0])
  else: dV = 0
      
  hSampling = np.zeros((len(pilot_v),len(pilot_h)),dtype=np.int32)
  vSampling = hSampling.copy()

  hSampling[:] = pilot_h[:]
  lf.hSampling = dH*hSampling
  vSampling = np.transpose(vSampling)
  vSampling[:] = pilot_v[:]
  vSampling = -dV*np.transpose(vSampling)
  lf.vSampling = vSampling
  lf.dH = dH
  lf.dV = dV  
  
  
  return lf


def depthToDisparity(lf_array,lf_camShifts,lf_intMatrices,lf_extMatrices,lf_camPositions,lf_focalLength,space_range):
  views_y = lf_array.shape[0]
  views_x = lf_array.shape[1]
  shape_y = lf_array.shape[2]
  shape_x = lf_array.shape[3]
  
  cam_dist = lf_camPositions[0][0][0]
  
  Ints = util.getMatrices(lf_intMatrices)
  Exts = util.getMatrices(lf_extMatrices,space_range)
  InvInts = util.getInverseMatrices(lf_intMatrices)
  InvExts = util.getInverseMatrices(lf_extMatrices)
  
  
  v_ref = np.matrix([shape_y/2*cam_dist,shape_x/2*cam_dist,cam_dist])
  v_ref = v_ref*InvInts[views_y/2][views_x/2]
  v_ref = np.matrix([v_ref[0,0],v_ref[0,1],v_ref[0,2],1])
  v_ref = v_ref*InvExts[views_y/2][views_x/2]
  v_ref = v_ref*Exts[views_y/2][views_x/2+1]
  v_ref = v_ref[0,0:3]
  v_ref = v_ref*Ints[views_y/2][views_x/2+1]

  
  p_ref = [v_ref[0,0]/v_ref[0,2],v_ref[0,1]/v_ref[0,2],v_ref[0,2]/v_ref[0,2]]

  shift = np.abs(shape_x/2-p_ref[0])

  #from LF.Utils.helpers import createH5
  minDisp = -5
  maxDisp = 5
  
  for vy in range(views_y):
    print "calc Disparity for subspace",vy," ... still to do:",views_y-vy
    for vx in range(views_x):
      
      #before = np.copy(lf_array[vy,vx,:,:,0])
      #if vx == 0:
        #print InvExts[vy][vx]
        #InvExts[vy][vx][3,1]*=-1
        #InvExts[vy][vx][3,2]*=-1
      #print "Exts",Exts,"--------------------------------------"
      #print "Ints:\n",Ints,"--------------------------------------" 
      #print "InvInts:\n",InvInts,"--------------------------------------" 
      #print "InvExts:\n",InvExts,"--------------------------------------" 
      fast._depthToDisparity(lf_array[vy,vx,:,:,0], Exts[vy][vx+1].view(np.ndarray), Ints[vy][vx].view(np.ndarray), InvExts[vy][vx].view(np.ndarray), InvInts[vy][vx].view(np.ndarray), shift, minDisp, maxDisp)
      #after = np.copy(lf_array[vy,vx,:,:,0])      
      #namet = "file_"+str(vy)+"_"+str(vx)+".h5"
      #createH5([{"name":"before","data":before,"dtype":np.float32},
      #          {"name":"after","data":after,"dtype":np.float32}                
       #         ],location="/home/sven/Desktop/bla",name=namet)
      
  return lf_array

    
