###################################
########    U S A G E    ########## 

if __name__ == "__main__":
  
  from LF.LFBase import *
  from LF.Utils import improc as ip
  from scipy.ndimage import median_filter
  import scipy as sp
  from DepthFromStructureTensor.depthFromStructureTensor import *
  from epiHandling import *

  #load light field  
  #lf = loadLF("/home/swanner/Packages/pymodules/LightFieldSuite/LF/Tests/Testdata/test_lf.lf")  
  #lf_array = np.copy(lf.LF)
  
  #load 
  #lf = h5.File("/home/swanner/Desktop/Movies2/Metallteil_speed-005/Metallteil_speed-005_1_57.h5","r")
  
  
  lf = loadLF("/home/swanner/Desktop/BoschVideoExperiments/Movies2/Stecker2_speed-005/Stecker2_speed-005_1_139.h5")
  noIpolRefocus(lf,-4)
  #ipolRefocus(lf,-4)
  
  lf_in = np.copy(lf["LF"])
  
  lf_array = np.zeros((1,lf_in.shape[0],lf_in.shape[1],lf_in.shape[2],lf_in.shape[3]),dtype=np.uint8)
  lf_array[0,:,:,:,:] = lf_in[:,:,:,:]


  #connect all the input slots
  DST = DepthFromStructureTensor()
  DST.inputLF.setValue(lf_array)
  DST.innerScale.setValue(1.1)
  DST.outerScale.setValue(3.3)
  DST.maxLabel.setValue(0.7)
  DST.minLabel.setValue(-0.4)
  DST.coherenceSmooth.setValue(0.5)
  
  #call for the entire light field and display center view
  #dest = DST.outputLF[0,:,100:600,200:800,:].allocate().wait()
  dest = DST.outputLF[:,:,260:830,220:1050,:].allocate().wait()
  
  """
  f = h5.File("/home/swanner/Desktop/Stecker2.h5","w")
  f.create_dataset("R",data=lf_array[:,:,260:830,220:1050,0])
  f.create_dataset("G",data=lf_array[:,:,260:830,220:1050,1])
  f.create_dataset("B",data=lf_array[:,:,260:830,220:1050,2])
  f.create_dataset("Depth",data=dest[:,:,:,:,0])
  f.close()"""
  
  
  res = dest[0,69,:,:,0]
  
  np.save("/home/swanner/Desktop/depth",res)
  
  #res = median_filter(res,9)
  sp.misc.imsave("/home/swanner/Desktop/depthTest.png",res)
  #print "mean",np.mean(res[610:630,480:500])
  #print "mean",np.mean(res[500:520,610:630] )
  #res[610:630,480:500] = -8
  #res[500:520,610:630] = -8
  #res = median_filter(res,5)
  ip.showImages([res],["result"])
  #call a for specific part of the light field and display center view
  #dest = DST.outputLF[:,:,100:300,100:300,:].allocate().wait()
  #ip.showImages([dest[0,100,:,:,0]],["result"])
