from LightField import *
from Blender import *
from LF.Utils.improc import showImages
import h5py as h5


if __name__ == "__main__":
  
  lf1 = fromBlender("./","./","test")
  lf2 = fromBlender("./","./","test_gray",1)
  
  print lf1.gt.shape
  print lf2.gt.shape
  
  lf3 = copyLF(lf1)  
  
  print lf3.gt.shape
  print lf3.channel
  
  saveLF(lf3,"./copy.lf")
  lf4 = loadLF("./copy.lf")
  
  f1=h5.File("./test_5x5_rgb.h5","r")
  f2=h5.File("./test_gray_5x5.h5","r")
  
  print "f1:"
  print 'vSampling',f1.attrs["vSampling"]
  print 'hSampling',f1.attrs["hSampling"]
  print 'xRes',f1.attrs["xRes"]
  print 'yRes',f1.attrs["yRes"]
  print 'vRes',f1.attrs["vRes"]
  print 'hRes',f1.attrs["hRes"]
  print 'dV',f1.attrs["dV"]
  print 'dH',f1.attrs["dH"]
  print 'channels',f1.attrs["channels"]
  print 'focalLength',f1.attrs["focalLength"]
  print 'camDistance',f1.attrs["camDistance"]
  
  print "\nf2:"
  print 'vSampling',f2.attrs["vSampling"]
  print 'hSampling',f2.attrs["hSampling"]
  print 'xRes',f2.attrs["xRes"]
  print 'yRes',f2.attrs["yRes"]
  print 'vRes',f2.attrs["vRes"]
  print 'hRes',f2.attrs["hRes"]
  print 'dV',f2.attrs["dV"]
  print 'dH',f2.attrs["dH"]
  print 'channels',f2.attrs["channels"]
  print 'focalLength',f2.attrs["focalLength"]
  print 'camDistance',f2.attrs["camDistance"]
  
  print "\nlf3 after copy"
  
  print 'vSampling',lf3.vSampling
  print 'hSampling',lf3.hSampling 
  print 'xRes',lf3.xRes
  print 'yRes',lf3.yRes
  print 'vRes',lf3.vRes
  print 'hRes',lf3.hRes
  print 'dV',lf3.dV
  print 'dH',lf3.dH
  print 'channels',lf3.channel
  print 'focalLength',lf3.focalLength 
  print 'camDistance',lf3.camDistance 
  
  print "\nlf4 after loading"
  print 'vSampling',lf4.vSampling
  print 'hSampling',lf4.hSampling 
  print 'xRes',lf4.xRes
  print 'yRes',lf4.yRes
  print 'vRes',lf4.vRes
  print 'hRes',lf4.hRes
  print 'dV',lf4.dV
  print 'dH',lf4.dH
  print 'channels',lf4.channel
  print 'focalLength',lf4.focalLength 
  print 'camDistance',lf4.camDistance 
  
  showImages([f1["LF"][2,2,:,:,:],f2["LF"][2,2,:,:,0],lf3.lf[2,2,:,:,:],lf4.lf[2,2,:,:,:]])
  print list(f1)
  print list(f2)
  print lf3.gt.shape
  showImages([f1["GT"][:,:],f2["GT"][:,:],lf3.gt[:,:],lf4.gt[:,:]])
  
  print lf3.dH
  print lf3.camDistance
  print lf3.focalLength
  disp = depthToDisparity(lf3.gt[:,:],lf3.dH,lf3.camDistance,lf3.focalLength)
  showImages([disp])
  
  
  
  
  
  
  
  