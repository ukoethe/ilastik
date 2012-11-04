import glob
import vigra
import types
import numpy as np
from sys import exit
import LightField as LF
from scipy.misc import imread



def depthToDisparity(depth,baseLine,camDistance,camAngle,degree=False):
  """
  @author: Sven Wanner
  @summary: generates a 2d depth image from a 2d disparity image
  @param disp: <2d ndarray> disparity image
  @param baseLine: <float> camera base line in blender units
  @param camDistance: <float> distance of blender cam to scene origin
  @param camAngle: <float> blender cam opening angle in degrees
  @return: 2d ndarray
  """
  imgWidth = depth.shape[1]
  
  if degree:   
    #convert angle to radians
    camAngle = camAngle/180.0*np.pi
  #calc value of the blender camera shift
  shift = 1.0/(2.0*camDistance*np.tan(camAngle/2.0))*baseLine
  #calc disparities
  disp = baseLine*imgWidth/(2.0*np.tan(camAngle/2.0)*(depth[:]))-shift*imgWidth
  
  return disp
  
  
  
def disparityToDepth(disp,baseLine,camDistance,camAngle):
  """
  @author: Sven Wanner
  @summary: generates a 2d disparity image from a 2d depth image
  @param disp: <2d ndarray> disparity image
  @param baseLine: <float> camera base line in blender units
  @param camDistance: <float> distance of blender cam to scene origin
  @param camAngle: <float> blender cam opening angle in degrees
  @return: 2d ndarray
  """
  imgWidth = disp.shape[1]
  
  #calc value of the blender camera shift
  shift = 1.0/(2.0*camDistance*np.tan(camAngle/2.0))*baseLine
  #calc depth
  depth = baseLine*imgWidth/(2.0*np.tan(camAngle/2.0)*(disp[:]+shift*imgWidth))
  
  return depth
  











def fromBlender(renderPath,outPath=None,outName="lf",channel=3):
  
  if renderPath[-1] != "/":
    renderPath += "/"
  params = parseLogfile(renderPath+"LF_logfile.txt")
  
  lf = LF.LightField()
  
  #generate light field from files
  lf.lf = genLightFieldfromFiles(renderPath+"images",angularRes=(params["steps"][0]*2+1,params["steps"][1]*2+1),channel=channel)
  
  #get all filenames and sort them
  files = []
  for f in glob.glob(renderPath+"depth/*.exr"):
    files.append(f)
    
  files.sort()
  
  assert len(files)!=0,"Fatal Error: No images found!"
  
  #set ground truth image
  cv_file = files[params["center_view"]]
  lf.gt = np.transpose(vigra.readImage(cv_file)[:,:,0].view(np.ndarray))
  
  #set attributes
  lf.yRes = lf.lf.shape[2]
  lf.xRes = lf.lf.shape[3]
  lf.vRes = params["steps"][0]*2+1
  lf.hRes = params["steps"][1]*2+1
  lf.channel = channel
  lf.focalLength = params["focal_length"]
  lf.camDistance = params["cam_distance"]
  
  #set uv Sampling
  grid_h = np.arange(-params["steps"][1],params["steps"][1]+1,dtype=np.float32)
  grid_v = np.arange(-params["steps"][0],params["steps"][0]+1,dtype=np.float32)
  
  if params["steps"][1] != 0:
    dH = params["space_range"][1]/float(params["steps"][1])
  else: dH = 0
  if params["steps"][0] != 0:
    dV = params["space_range"][0]/float(params["steps"][0])
  else: dV = 0
      
  lf.dV = dV
  lf.dH = dH
  
  hSampling = np.zeros((len(grid_v),len(grid_h)),dtype=np.int32)
  vSampling = hSampling.copy()

  hSampling[:] = grid_h[:]
  lf.hSampling = dH*hSampling
  vSampling = np.transpose(vSampling)
  vSampling[:] = grid_v[:]
  vSampling = -dV*np.transpose(vSampling)
  lf.vSampling = vSampling
  
  #if outpath is not None save lf
  if outPath is not None:
    if outName.find(".h5") == -1:
      outName += "_"+str(params["steps"][0]*2+1)+"x"+str(params["steps"][1]*2+1)
      if channel==3:
        outName += "_rgb"
      outName += ".h5"
    else:
      tmp = outName.split(".h5")
      outName = tmp[0]+"_"+str(params["steps"][0]*2+1)+"x"+str(params["steps"][1]*2+1)
      if channel==3:
        outName += "_rgb"
      outName += ".h5"
    LF.saveLF(lf,outPath+outName)
  
  return lf
  
  
def genLightFieldfromFiles(location,filetype="png",angularRes=None,channel=3):
  """
  @author: Sven Wanner
  @summary: generates a light field array from blender images
  @param location: <string> location of the rendered files
  @param filetype <string> image type default: png
  @param angularRes: <int tuple> vertical and horizontal amount of cam positions default:None
  @param channel: <int> define output color mode, grayscale 1, color 3, default: 3
  @return: 5d ndarray
  """
  
  #get all filenames and sort them
  files = []
  for f in glob.glob(location+"/*."+filetype):
    files.append(f)
    
  files.sort()
  
  assert len(files)!=0,"Fatal Error: No images found!"
  assert angularRes != None, "Fatal Error: No angular resolution specified!"

  img = imread(files[0])[:,:,0:3]
  
  
  if (type(angularRes) is types.ListType or type(angularRes) is types.TupleType) and len(angularRes) == 2:
    lf = np.zeros((angularRes[0],angularRes[1],img.shape[0],img.shape[1],channel),dtype=np.uint8)
    
    n=0
    for v in range(angularRes[0]):
      for h in range(angularRes[1]):
        img = imread(files[n])[:,:,0:3]
        if channel == 1:
          tmp = np.zeros((img.shape[0],img.shape[1],channel),dtype=np.uint8)
          tmp[:,:,0] = 0.3*img[:,:,0]+0.59*img[:,:,1]+0.11*img[:,:,2]
          img = tmp
        lf[v,h,:,:,:] = img[:,:,:]
        n+=1
  else:
    print "Fatal Error: Incorrect angular resolution specified!"
    exit()
  
  return lf
      

  

def parseLogfile(fname):
  """
  @author: Sven Wanner
  @summary: parse a blender LightField Plugin Logfile 
  @param fname: <string> filename
  @return: dict holding parsed parameter
  """
  
  try:  
    lfile = open(fname)
  except:
    print "Fatal Error: No Logfile found!"
    exit()
    
  params = {
            "space_range":[0,0],
            "steps":[0,0],
            "focal_length":None,
            "center_view":None,
            "cam_distance":None
            }
  
  while 1:
    line = lfile.readline()
    if not line:
        break
    
    if line.find("space_range_x") != -1:
      params["space_range"][1] = float(line[line.find(":")+1:])
    if line.find("space_range_y") != -1:
      params["space_range"][0] = float(line[line.find(":")+1:])
    if line.find("steps_x") != -1:
      params["steps"][1] = int(line[line.find(":")+1:])
    if line.find("steps_y") != -1:
      params["steps"][0] = int(line[line.find(":")+1:])
    if line.find("focal_length [rad]") != -1:
      params["focal_length"] = float(line[line.find(":")+1:])
    if line.find("cam_distance") != -1:
      params["cam_distance"] = float(line[line.find(":")+1:])
      
  params["center_view"] = params["steps"][0]*(2*params["steps"][1]+1)+params["steps"][1]
  
  return params
  




  


