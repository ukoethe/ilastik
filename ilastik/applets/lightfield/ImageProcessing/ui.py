import numpy as np
import pylab as plt
import matplotlib.cm as cm
import matplotlib.pyplot as pyplt
import matplotlib.mlab as mlab
import types
import libui as fast
from types import StringType





def overlayShow(im,overlays,allowedError,amount,alpha=0.8,title="",saveTo=None,cmap=None,interpolation='nearest',show=True):
  if cmap=="gray":
    cmap = cm.gray
  elif cmap=="jet":
    cmap=cm.jet
  elif cmap=="hot":
    cmap=cm.hot
  elif cmap=="autumn":
    cmap=cm.autumn
    
  img = np.copy(im).astype(np.uint8)
  
  
  for overlay in overlays:
    fast._colorOverlay(img,overlay.astype(np.uint8),alpha,img)
        
  fig = plt.figure()
  
  ax = fig.add_subplot(111)
  
  title += "\n"+str(round(amount,2))+"% of pixels have error less than "+str(allowedError*100)+"%"
  ax.set_title(title)
  ax.set_xlabel("("+str(np.amin(im))+","+str(np.amax(im))+") mean="+str(np.mean(im)) )
  if cmap is not None:
    ax.imshow(img,interpolation=interpolation,cmap=cmap)
  else:
    ax.imshow(img,interpolation=interpolation)
  
  if saveTo is not None and type(saveTo) is StringType:
    show = False
    if saveTo.find(".png") == -1:
      saveTo+=".png"
    print "Save figure to:",saveTo
    plt.savefig(saveTo, transparent = False)
  
  if show: plt.show()
  


def show(imgs,labels=[""],interpolation="nearest",cmap="gray",show=True,transpose=False):
    """
    2D image viewer: arg1 image<ndarray> or list of them, arg2 labels<String> or list of them, arg3 interpolation (default:'nearest')
    """
    if transpose:
      for i in range(len(imgs)):
        imgs[i] = np.transpose(imgs[i])
  
    
    if cmap=="gray":
        cmap = cm.gray
    elif cmap=="jet":
        cmap=cm.jet
    elif cmap=="hot":
        cmap=cm.hot
    elif cmap=="autumn":
        cmap=cm.autumn
        
    fig = plt.figure()
    
    if str(type(imgs))=="<type 'numpy.ndarray'>":
        label = ""
        if type(labels)==types.ListType: label = labels[0]
        elif type(labels)==types.StringType: label = labels
        
        ax = fig.add_subplot(111)
        ax.set_title(label)
        ax.set_xlabel("("+str(np.amin(imgs))+","+str(np.amax(imgs))+") mean="+str(np.mean(imgs)) )
        ax.imshow(imgs,interpolation=interpolation,cmap=cmap)
    
    elif type(imgs)==types.ListType and len(imgs) < 5:
        if len(labels)<len(imgs):
            diff=len(imgs)-len(labels)
            for i in range(diff):
                labels.append("")    
        
        n=111
        if len(imgs) == 2:
            n+=10
        if len(imgs) > 2:
            n+=110
            
        for i in range(len(imgs)):
            ax = fig.add_subplot(n)
            ax.set_title(labels[i])
            ax.set_xlabel("("+str(np.amin(imgs[i]))+","+str(np.amax(imgs[i]))+") mean="+str(np.mean(imgs[i])) )
            ax.imshow(imgs[i],interpolation=interpolation,cmap=cmap)
            n+=1
    else: print "Wrong parameter type, need ndarray or list of them"
        
    if show: plt.show()
    
    
    
def showVectorImage(fx,fy,title="",gap=1,show=True):
    X,Y = np.meshgrid( range(fx.shape[1]),range(fx.shape[0]))
    plt.figure()
    Q = plt.quiver( X[::gap, ::gap], Y[::gap, ::gap], fx[::gap, ::gap], fx[::gap, ::gap],pivot='mid', color='r', units='x', headaxislength=3)
    qk = plt.quiverkey(Q, 0.5, 0.03, 1, r'', fontproperties={'weight': 'bold'})
    plt.plot( X[::gap, ::gap], Y[::gap, ::gap], 'k.')
    
    plt.title(title)
    if show: plt.show()
    
    
    
def gridPlot(x,y,z,xLabel="",yLabel="",title="",save=None,show=True):
  plt.figure()
        
  X,Y = plt.meshgrid(x, y)
  
  argmax = np.where(z==np.amax(z))
  
  optInner = str(y[argmax[0][0]]) 
  optOuter = str(x[argmax[1][0]]) 
  
  title = title+"\nOptimum at inner: "+optInner+" outer: "+optOuter
  
  plt.pcolor(X, Y, z)
  plt.colorbar()
  plt.axis([x[0],x[-1],y[0],y[-1]])
  plt.title(title)
  plt.xlabel(xLabel)
  plt.ylabel(yLabel)
  if save is not None:
    show=False
    if save == "":
      name = "./gridSearchResult.svg"
    else:
      name = save
      if save.find(".svg")==-1:
        name+=".svg"

      plt.savefig(name, transparent = True)
  if show:
    plt.show()
    
    
def plotErrorHistogram(lf,lf2=None,tv={"lambda":0.5,"iter":300},leftLimit=None,rightLimit=None,distance=0.1,withStd=False,save=None,title="Error Histogram",name=""):
  """
  @author: Sven Wanner
  @brief: takes a lightfield and plots the error histogram mean error over disparity
  @param lf: <object> LightField instance
  @param lf2: <object> optional second LightField instance, default:None 
  @param leftLimit: <float> Histogram left limit, default:None make use of min disparity value
  @param rightLimit: <float> Histogram right limit, default:None make use of max disparity value
  @param distance: <float> discretization of disparity space, default:0.1
  @param withStd: <bool> plots the standard deviation, default:False
  @param save: <str> filepath/filename, default: None only shows the image
  @param title: <str> plot title, default: Error Histogram
  """
  
  from LFLib.Blender import depthToDisparity
  
  if lf.depth is None:
    print "Cannot evaluate without depth data!"
    return
  if lf.gt is None:
    print "Cannot evaluate without ground truth!"
    return
  
  if lf2 is not None and lf2.gt is not None and lf2.depth is not None:
    doublePlot = True
  else:
    doublePlot = False
  
  gt_inDisp = depthToDisparity(lf.gt,lf.dH,lf.camDistance,lf.focalLength,lf.xRes)
  mse = np.abs(np.abs(gt_inDisp[:])-np.abs(lf.depth[:]))
  
  if doublePlot:
    gt_inDisp2 = depthToDisparity(lf2.gt,lf2.dH,lf2.camDistance,lf2.focalLength,lf2.xRes)
    mse2 = np.abs(np.abs(gt_inDisp2[:])-np.abs(lf2.depth[:]))
  
  if leftLimit is None:
    leftLimit = int(np.floor(np.amin(gt_inDisp)))
    print "Use leftLimit:",leftLimit
  if rightLimit is None:
    rightLimit = int(np.ceil(np.amax(gt_inDisp)))
    print "Use rightimit:",rightLimit
  
  y = mse.flatten()
  x = gt_inDisp.flatten()
  
  X = np.arange(leftLimit,rightLimit+distance,distance)
  X[X.shape[0]/2] = 0
  numOfBins = X.shape[0]
  
  Y = np.zeros(numOfBins,dtype=np.float32)
  Std = np.zeros(numOfBins,dtype=np.float32)
  
  if doublePlot:
    y2 = mse2.flatten()
    x2 = gt_inDisp2.flatten()
    
    Y2 = np.zeros(numOfBins,dtype=np.float32)
    Std2 = np.zeros(numOfBins,dtype=np.float32)
  
  for n in range(numOfBins): 
    sign = 1
    if X[n]<0:
      sign = -1
      
    if n!=0 and n!=numOfBins-1:
      left = X[n]+sign*distance/2.0
      right = X[n]-sign*distance/2.0
    elif n==0:
      left = -10000
      right = leftLimit+distance/2.0
    elif n==numOfBins-1:
      right = 10000
      left = rightLimit-distance/2.0
    
    
    vals = []
    vals2 = []
    for i in xrange(x.shape[0]):

      dispval = x[i] 
      if doublePlot:
        dispval2 = x2[i]
      
      if sign < 0:
        if dispval > left and dispval <= right:
          vals.append(y[i])
        
        if doublePlot:
          if dispval2 > left and dispval2 <= right:
            vals2.append(y2[i])
        
      if sign > 0:
        if dispval < left and dispval >= right:
          vals.append(y[i])
          
        if doublePlot:
          if dispval2 < left and dispval2 >= right:
            vals2.append(y2[i])
             
    if len(vals)!=0:
      Y[n] = np.mean(vals)
      Std[n] = np.std(vals)
      
    if doublePlot:
      if len(vals2)!=0:
        Y2[n] = np.mean(vals2)
        Std2[n] = np.std(vals2)
      
    print "--------------------------------------------"
    print "For Disparity = ",X[n]," I found ",len(vals)," values summed up to Y[",n,"] =",Y[n]," with a Std of",Std[n]
    print "-------------------------------------------\n"
      
  
  #fig = plt.figure()
  #ax = fig.add_subplot(111)
  
  
  if withStd == False:
    Std = None
    
  fname = save+"_X.npy"
  np.save(save,X)
  fname = save+"_Y.npy"
  np.save(save,Y)
    
  if doublePlot:
    if withStd == False:
      Std2 = None
    
    fname = save+"_Y2.npy"
    np.save(save,Y2)
    b2 = pyplt.bar(X, Y2, distance, color='r', yerr=Std2)
    
  b = pyplt.bar(X, Y, distance, color='g', yerr=Std)
  pyplt.ylabel('mean error ||d|-|gt||')
  pyplt.xlabel('disparity in [px]')
  pyplt.title(title)
  
#  if doublePlot:
#    pyplt.legend( (b2[0], b[0]), ('noise', 'no noise') )
#  else:
#    pyplt.legend( (b[0]), (name) )

  if save is None:
    pyplt.show()
  else:
    if save.find(".svg") == -1:
      save+=".svg"
    pyplt.savefig(save, transparent = True)