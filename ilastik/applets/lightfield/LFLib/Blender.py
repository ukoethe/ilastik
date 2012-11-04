import glob
import vigra
import types
import numpy as np
from sys import exit
import LightField as LF
from scipy.misc import imread
from scipy import meshgrid
import os

from ImageProcessing.ui import show


def depthToDisparity(depth,baseLine,camDistance,camAngle,xRes,degree=False):
  """
  @author: Sven Wanner
  @brief: generates a 2d depth image from a 2d disparity image
  @param disp: <2d ndarray> disparity image
  @param baseLine: <float> camera base line in blender units
  @param camDistance: <float> distance of blender cam to scene origin
  @param camAngle: <float> blender cam opening angle in degrees
  @return: 2d ndarray
  """

  if degree:   
    #convert angle to radians
    camAngle = camAngle/180.0*np.pi
  #calc value of the blender camera shift
  shift = 1.0/(2.0*camDistance*np.tan(camAngle/2.0))*baseLine
  #calc disparities
  disp = baseLine*xRes/(2.0*np.tan(camAngle/2.0)*(depth[:]))-shift*xRes
  
  return disp
  
  
  
def disparityToDepth(disp,baseLine,camDistance,camAngle,xRes,degree=False):
  """
  @author: Sven Wanner
  @brief: generates a 2d disparity image from a 2d depth image
  @param disp: <2d ndarray> disparity image
  @param baseLine: <float> camera base line in blender units
  @param camDistance: <float> distance of blender cam to scene origin
  @param camAngle: <float> blender cam opening angle in degrees
  @return: 2d ndarray
  """
  
  if degree:   
    #convert angle to radians
    camAngle = camAngle/180.0*np.pi
  #calc value of the blender camera shift
  shift = 1.0/(2.0*camDistance*np.tan(camAngle/2.0))*baseLine
  #calc depth
  depth = baseLine*xRes/(2.0*np.tan(camAngle/2.0)*(disp[:]+shift*xRes))
  
  return depth
  


def getMeta(renderPath,channel):
  """
  @author: Frederik Claus
  @summary: Returns all meta data of LF
  """
  params = parseLogfile(os.path.join(renderPath,"LF_logfile.txt"))
  vRes = params["steps"][0]*2+1;
  hRes = params["steps"][1]*2+1;
  imRes = getResolution(os.path.join(renderPath,"images"))
  yRes = imRes[0]
  xRes = imRes[1]
  params["shape"] = (vRes,hRes,yRes,xRes,channel)
  
  return params

def getResolution(path):
  files = getImages(path, "png")
  try:
    img = imread(files[0])[:,:]
    return (img.shape[0],img.shape[1])
  except:
    print "Could not read image"


def getImages(path,filetype):
  files = []
  for f in glob.glob(os.path.join(path,"*."+filetype)):
    files.append(f)
    
  files.sort()
  return files





def fromBlender(renderPath,outPath=None,outName="lf",channel=3,withGT=True):
  """
  @author: Sven Wanner
  @brief: generates a light field from blender render results using a Logfile
  @param renderPath: <string> directory of render results, must contain images and depth directory as well as a LF_Logfile.txt
  @param outPath: <string> putput path, if None the light field is only returned, default:None
  @param outName: <string> name of the light field file, default:"lf"
  @param channel: <int> number of channels, 3 -> rgb, 1 -> gray, default:3
  @param withGT: <bool> creating ground truth switch, default:True
  @return: 5d ndarray
  """
  if renderPath[-1] != "/":
    renderPath += "/"
  
  params = parseLogfile(renderPath+"LF_logfile.txt")
  
  lf = LF.LightField()
  
  #generate light field from files
  lf.lf = genLightFieldfromFiles(renderPath+"images",angularRes=(params["steps"][0]*2+1,params["steps"][1]*2+1),channel=channel)
  
  #get all filenames and sort them
  files = []
  for f in glob.glob(renderPath+"depth/*.exr"):
    print f
    files.append(f)
    
  files.sort()
  
  assert len(files) != 0,"Fatal Error: No images found!"
  
  if withGT:
    #set ground truth image
    cv_file = files[params["center_view"]]
    lf.gt = np.transpose(vigra.readImage(cv_file)[:,:,0].view(np.ndarray))
  
  #set attributes
  lf.yRes = lf.lf.shape[2]
  lf.xRes = lf.lf.shape[3]
  lf.vRes = params["steps"][0]*2+1
  lf.hRes = params["steps"][1]*2+1
  lf.channels = channel
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
  
  lf.hSampling,lf.vSampling = meshgrid(grid_h,grid_v)
  lf.vSampling*=dV
  lf.hSampling*=dH
  
  print "\ngenerate Light Field fromBlender:"
  print "vRes",lf.vRes
  print "hRes",lf.hRes
  print "yRes",lf.yRes
  print "xRes",lf.xRes
  print "dV",lf.dV
  print "dH",lf.dH
  print "focalLength",lf.focalLength
  print "camDistance",lf.camDistance
  print "hSampling[0,:]",lf.hSampling[0,:]
  print "vSampling[:,0]",lf.vSampling[:,0]
  
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
      
    if outPath[-1] != "/":
      outPath+="/"
    LF.saveLF(lf,outPath+outName)
  
  return lf
  
  
def genLightFieldfromFiles(location,filetype="png",angularRes=None,channel=3):
  """
  @author: Sven Wanner
  @brief: generates a light field array from blender images
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
  print len(files)
  

  assert len(files) != 0,"Fatal Error: No images found!"
  assert angularRes != None, "Fatal Error: No angular resolution specified!"

  try:
    img = imread(files[0])[:,:,0:3]
    rgb = True
  except:
    img = imread(files[0])[:,:]
    rgb = False
    channel = 1
  
  if (type(angularRes) is types.ListType or type(angularRes) is types.TupleType) and len(angularRes) == 2:
    lf = np.zeros((angularRes[0],angularRes[1],img.shape[0],img.shape[1],channel),dtype=np.uint8)
    
    n=0
    for v in range(angularRes[0]):
      for h in range(angularRes[1]):
        if rgb:
          img = imread(files[n])[:,:,0:3]
        else:
          img = imread(files[n])[:,:]
        if channel == 1 and rgb:
          tmp = np.zeros((img.shape[0],img.shape[1],channel),dtype=np.uint8)
          tmp[:,:,0] = 0.3*img[:,:,0]+0.59*img[:,:,1]+0.11*img[:,:,2]
          img = tmp
        
        if rgb:
          lf[v,h,:,:,:] = img[:,:,:]
        else:
          lf[v,h,:,:,0] = img[:,:]
        n+=1
  else:
    print "Fatal Error: Incorrect angular resolution specified!"
    exit()
  
  return lf
      

  

def parseLogfile(fname):
  """
  @author: Sven Wanner
  @brief: parse a blender LightField Plugin Logfile 
  @param fname: <string> filename
  @return: dict holding parsed parameter
  """
  
  try:  
    print "try to load LF_Logfile.txt:",fname," ",
    lfile = open(fname)
    print "ok"
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
  



def fillEntireGT(lf,gtloc,outname=None):
  
  import glob
  
  files = []
  for fname in glob.glob(gtloc+"*.exr"): 
    files.append(fname)
    
  files.sort()
  
  print files
  
  n=0
  d = np.zeros((lf.vRes,lf.hRes,lf.yRes,lf.xRes),dtype=np.float32)
  for i in range(lf.vRes):
    for j in range(lf.hRes):
      tmp = vigra.readImage(files[n])[:,:,0].view(np.ndarray)
      d[i,j,:,:] = np.transpose(tmp)
      n+=1
      
  lf.gt = d
  if outname is not None:
    if outname.find(".h5") == -1:
      outname+=".h5"
    LF.saveLF(lf,outname)


