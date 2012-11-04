import fast
import numpy as np
import vigra

def toList(string):
  return map(float,string[1:-1].split(','))
  
  
def o2ListToList(string):
  string = string[1:-1]
  string = string.replace("], [","];[")
  list=[]
  while string.find(";")!=-1:
    temp=string.partition(";")
    list.append(temp[0])
    string=temp[2]
  list.append(string)

  res=[]
  for item in list:
    res.append(toList(item))   
  return res   
  
  
def o3ListToList(string):
  string = string[1:-1]
  string = string.replace("]], [[","]];[[")
  list=[]
  while string.find(";")!=-1:
    temp=string.partition(";")
    list.append(temp[0])
    string=temp[2]
  list.append(string)
  
  res = []
  for i in range(len(list)):
    res.append(o2ListToList(list[i]))
    
  return res
  
  
def getMatrices(ndarray,space_range=-1):
  mats = []
  
  for i in range(ndarray.shape[0]):
    tmp = []
    for j in range(ndarray.shape[1]):
      tmp.append(np.matrix(ndarray[i,j,:,:]))
      if j==ndarray.shape[1]-1 and space_range !=-1:
        lm = np.copy(np.matrix(ndarray[i,j,:,:]))
        
        sign1 = 1
        if lm[3,0] < 0:
          sign1 = -1
        sign2 = 1
        if lm[3,1] < 0:
          sign2 = -1
        
        lm[3,0] += sign1*space_range
        lm[3,1] += sign2*space_range
        tmp.append(lm)
    mats.append(tmp)
    
  return mats



def getInverseMatrices(ndarray):
  mats = []
  
  for i in range(ndarray.shape[0]):
    tmp = []
    for j in range(ndarray.shape[1]):
      mat = np.matrix(ndarray[i,j,:,:])
      tmp.append(np.linalg.inv(mat))
    mats.append(tmp)
    
  return mats
  

def parseLogfile(path):

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
      cam_rotation = toList(arr_str)
    if line.find("cam_shifts") != -1:
      arr_str = line[line.find(":")+1:]
      arr_str = arr_str.replace("\n","")
      cam_shifts = o2ListToList(arr_str)
    if line.find("positions") != -1:
      arr_str = line[line.find(":")+1:]
      arr_str = arr_str.replace("\n","")
      cam_positions = o2ListToList(arr_str)
    if line.find("scene_dimensions") != -1:
      arr_str = line[line.find(":")+1:]
      arr_str = arr_str.replace("\n","")
      scene_dimensions = toList(arr_str)
    if line.find("scene_center") != -1:
      arr_str = line[line.find(":")+1:]
      arr_str = arr_str.replace("\n","")
      scene_center = toList(arr_str)
    if line.find("focal_length [rad]") != -1:
      focal_length_rad = float(line[line.find(":")+1:])
    if line.find("resolution") != -1:
      arr_str = line[line.find(":")+1:]
      arr_str = arr_str.replace("\n","")
      resolution = toList(arr_str)
    if line.find("cam_matrix_ext") != -1:
      arr_str = line[line.find(":")+1:]
      arr_str = arr_str.replace("\n","")
      cam_matrix_ext = o3ListToList(arr_str)
    if line.find("cam_matrix_int") != -1:
      arr_str = line[line.find(":")+1:]
      arr_str = arr_str.replace("\n","")
      cam_matrix_int = o3ListToList(arr_str)
  
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
            "cam_matrix_ext":cam_matrix_ext,
            "center_view":[steps[0],steps[1]]
  }
  
  return params


def depthToDisparity(depthimage,lf_camShifts,lf_intMatrices,lf_extMatrices,lf_camPositions,lf_focalLength,space_range,center_view):

  shape_y = depthimage.shape[0]
  shape_x  = depthimage.shape[1]
  
  cam_dist = lf_camPositions[0][0][0]
  
  Ints = getMatrices(lf_intMatrices)
  Exts = getMatrices(lf_extMatrices,space_range)
  InvInts = getInverseMatrices(lf_intMatrices)
  InvExts = getInverseMatrices(lf_extMatrices)
  
  v_ref = np.matrix([shape_y/2*cam_dist,shape_x/2*cam_dist,cam_dist])
  v_ref = v_ref*InvInts[center_view[0]][center_view[1]]
  v_ref = np.matrix([v_ref[0,0],v_ref[0,1],v_ref[0,2],1])
  v_ref = v_ref*InvExts[center_view[0]][center_view[1]]
  v_ref = v_ref*Exts[center_view[0]][center_view[1]+1]
  v_ref = v_ref[0,0:3]
  v_ref = v_ref*Ints[center_view[0]][center_view[1]+1]

  
  p_ref = [v_ref[0,0]/v_ref[0,2],v_ref[0,1]/v_ref[0,2],v_ref[0,2]/v_ref[0,2]]

  shift = np.abs(shape_x/2-p_ref[0])

  minDisp = -5
  maxDisp = 5
  
  disparity = np.copy(depthimage)
  fast._depthToDisparity(disparity, Exts[center_view[0]][center_view[1]+1].view(np.ndarray), Ints[center_view[0]][center_view[1]].view(np.ndarray), InvExts[center_view[0]][center_view[1]].view(np.ndarray), InvInts[center_view[0]][center_view[1]].view(np.ndarray), shift, minDisp, maxDisp)

  return disparity
  
  
def depth2Disp(logfileDir):
  params = parseLogfile(logfileDir)
  print "center_view",params["center_view"]
  
  cvimg = (2*params["center_view"][0]+1)*(2*params["center_view"][1]+1)/2
  logfileDir+="depth/%.3i_0001.exr"%cvimg
  print "use groundtruth file:",logfileDir
  depthimage = np.transpose(vigra.readImage(logfileDir).view(np.ndarray)[:,:,0])

  steps = params["steps"]  
  lf_camShifts = np.zeros((2*steps[0]+1,2*steps[1]+1,2),dtype=np.float32)
  lf_camPositions = np.zeros((2*steps[0]+1,2*steps[1]+1,3),dtype=np.float32)
  lf_intMatrices = np.zeros((2*steps[0]+1,2*steps[1]+1,3,3),dtype=np.float32)
  lf_extMatrices = np.zeros((2*steps[0]+1,2*steps[1]+1,4,4),dtype=np.float32)
  
    
  n=0
  for i in range(2*steps[0]+1):
    for j in range(2*steps[1]+1):
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

  disparity = depthToDisparity(depthimage,lf_camShifts,lf_intMatrices,lf_extMatrices,lf_camPositions,params["focal_length_rad"],params["space_range"][0]/steps[1],params["center_view"])
  
  return disparity
  
  

  
  
  
  
  
  
  
  
  
if __name__ == "__main__":
  disparity = depth2Disp(logfileDir="/home/swanner/data/LightFieldData/Blender/Scenes/JournalPaperScenes/NoisyPlanes/9x9/")
