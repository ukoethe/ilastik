import vigra
import threading
import numpy as np
from time import time

#import functions written in cython
import chooseEigenvectors as cE
import coherenceMerge as cM

#import lazyflow stuff
from lazyflow.graph import Operator, InputSlot, OutputSlot




class DepthFromStructureTensor(Operator):
  """
  @summary: This lazyflow operator needs a 5 dimensional light field as input,
  as well as several parameter slots have to be set. (see below)
  The output is a light field of same shape as the input but
  as single channel float32 containing the labeled disparitities.
  """
  inputLF = InputSlot()  # define lf input slot -> 5d numpy array lf[h,v,y,x,channel]
  outerScale = InputSlot() # define outerscale of structure tensor input slot -> float > 0
  innerScale = InputSlot() # define innerscale of structure tensor input slot -> float > 0
  maxLabel = InputSlot() # define maximum label input slot -> float 
  minLabel = InputSlot() # define minimum label input slot -> float 
  coherenceSmooth = InputSlot() # define coherence smooth value input slot -> float > 0 
  outputLF = OutputSlot() # define label output slot
  
  def execute(self, slot, roi, result):
    # the following two lines query the inputs of the
    # operator for the specififed region of interest
    lf = self.inputLF.get(roi).wait()
    
    params = {"inner":self.innerScale.value,"outer":self.outerScale.value,"maxLabel":self.maxLabel.value,"minLabel":self.minLabel.value,"coherenceSmooth":self.coherenceSmooth.value}   
    
    labeled_h, labeled_v = label(lf,params)
    labeled, coherence = cM._coherenceMerge(labeled_h[:,:,:,:,1],labeled_v[:,:,:,:,1],labeled_h[:,:,:,:,0],labeled_v[:,:,:,:,0])
    
    result[:,:,:,:,0] = labeled[:]
    
    
  def setupOutputs(self):
    # query the shape of the operator inputs
    # by reading the input slots meta dictionary
    shapeLF = self.inputLF.meta.shape

    # setup the meta dictionary of the output slot
    self.outputLF.meta.shape = shapeLF

    # setup the dtype of the output slot
    self.outputLF.meta.dtype = np.float32
    
    
    
    
    


class LabelThread(threading.Thread):
  """
  @summary: This class threads the labeling in horizontal and vertical direction into paralell threads
  """  
  def __init__(self, lf, params, direction):
    self._result = np.zeros((lf.shape[0],lf.shape[1],lf.shape[2],lf.shape[3],2),dtype=np.float32)
    self._lf = lf
    self._params = params
    self._direction = direction
    threading.Thread.__init__(self)
    
  def run(self):
    labelDirection(self._lf,self._result,self._params,self._direction)
    
  def getResult(self):
    return self._result
     



def label(lf,params):
  """
  @summary: threaded segmentation routine returning dataterms of both segmentation directions
  @param lf:<4d ndarray> input light field
  @param params:<dictionary> parameter: {"inner","outer","maxLabel","minLabel"}
  @return: dataterm1 <5d ndarray>, dataterm2 <5d ndarray> dataterm[:,:,:,:,0]:depth,dataterm[:,:,:,:,1]:coherence
  """
  
  result_u = np.zeros((lf.shape[0],lf.shape[1],lf.shape[2],lf.shape[3],2),dtype=np.float32)
  result_v = np.zeros((lf.shape[0],lf.shape[1],lf.shape[2],lf.shape[3],2),dtype=np.float32)

  t0=time()
  
  threadLock = threading.Lock()
  threads = []
  
  if lf.shape[1] > 1:
    thread1 = LabelThread(lf,params,'u')
  if lf.shape[0] > 1:
    thread2 = LabelThread(lf,params,'v')
  
  if lf.shape[1] > 1:
    thread1.start()
  if lf.shape[0] > 1:
    thread2.start()
  
  if lf.shape[1] > 1:
    threads.append(thread1)
  if lf.shape[0] > 1:
    threads.append(thread2)
  
  for t in threads:
      t.join()
  
  if lf.shape[1] > 1:
    result_u = thread1.getResult()
  if lf.shape[0] > 1:
    result_v = thread2.getResult()
    result_v[:,:,:,:,0]*=-1 #invert v channel TODO check why!
  
  print "duration segmentation",time()-t0
    
  return result_u, result_v
  
  
  



def labelDirection(lf,depth,params,direction):
  """
  @summary: labels depth regions on epipolar plane space of an 4d input lightfield 
  @param lf:<4d ndarray> input light field
  @param depth:<5d ndarray> output depth and coherence structure... 
  depth[:,:,:,:,0]:depth in u, 
  depth[:,:,:,:,1]:coherence in u,
  depth[:,:,:,:,2]:depth in v, 
  depth[:,:,:,:,3]:coherence in v,
  @param params:<dictionary> parameter: {"inner","outer","maxLabel","minLabel","coherenceSmooth}
  @param direction:<char> segementation direction 'u','v'
  """
  if direction == 'u':
    status = lf.shape[0]
    angles = lf.shape[0]
    spatials = lf.shape[2]
  elif direction == 'v':
    status = lf.shape[1]
    angles = lf.shape[1]
    spatials = lf.shape[3]
    
    
  for angle in range(angles):
    print status," ",direction,"subspaces remain"
    status -= 1
    
    if direction == 'u':
      subLF = getSubspace(lf,u=angle)
    elif direction == 'v':
      subLF = getSubspace(lf,v=angle)
    
    for spatial in range(spatials):
      if direction == 'u':
        epi = subLF[:,spatial,:]
      elif direction == 'v':
        epi = subLF[:,:,spatial]
  
      try:
        d,c = getDirections(img=epi, inner=params["inner"], outer=params["outer"], maxLabel=params["maxLabel"], minLabel=params["minLabel"],coherenceSmooth=params["coherenceSmooth"],direction=direction)
      except Exception as e:
        print "\n\nERROR in label!"
        import traceback
        traceback.print_exc()
        import sys
        sys.exit()
       
      if direction == 'u':
        depth[angle,:,spatial,:,0] = d[:,:]
        depth[angle,:,spatial,:,1] = c[:,:]
      elif direction == 'v':     
        depth[:,angle,:,spatial,0] = d[:,:]
        depth[:,angle,:,spatial,1] = c[:,:]
    
    



def getDirections(img,inner,outer,maxLabel,minLabel,coherenceSmooth,direction):
  """
  @summary: Calculates the directions of structures using the 
  structure tensor and returns them as well as the corresponding coherence
  @param img:<2d ndarray> input image
  @param inner:<float> inner scale of structure tensor
  @param outer:<float> outer scale of structure tensor
  @param maxLabel:<float> maximum Labelarity or allowed structure slope
  @param minLabel:<float> minimum Labelarity or allowed structure slope 
  @return: directions:<2d ndarray>, coherence:<2d ndarray>
  """
  try:  
    tensor,coh = structureTensor(img,inner,outer,coherenceSmooth,with_coherence=True)
    dirs = directionsFromTensor(tensor)
  except Exception as e:
    print "\n\nsERROR in getDirections tensor and coherence evaluation!"
    import traceback
    traceback.print_exc()
    import sys
    sys.exit()
  
  d = dirs[:,:,1]/(dirs[:,:,0]+1e-16)
  if direction == 'u':
    np.place(d,d>maxLabel,maxLabel)
    np.place(d,d<minLabel,minLabel)
  if direction == 'v':
    np.place(d,-d>maxLabel,-maxLabel)
    np.place(d,-d<minLabel,-minLabel)

  return d,coh



def getSubspace(lf,v=None,u=None):
  """
  @summary: Returns u/v subspaces of a 4D light field
  @param v:<int>[None] angular in v direction
  @param u:<int>[None] angular in u direction
  @return u or v: depends on not None parameter
  """
  if u is not None and v is None:
    try:
      return lf[u,:,:,:].astype(np.float32)
    except Exception as e:
      print "\n\nERROR in v getSubspace!"
      import traceback
      traceback.print_exc()
      import sys
      sys.exit()
  elif v is not None and u is None:
    try:
      return lf[:,v,:,:].astype(np.float32)
    except Exception as e:
      print "\n\nERROR in u getSubspace!"
      import traceback
      traceback.print_exc()
      import sys
      sys.exit()
    
    


def structureTensor(img,inner,outer,coherenceSmooth,with_coherence=False):
  """
  @summary: Calculates structure tensor and coherence of the structure tensor
  @param inner:<float> inner smoothing scale of the structure tensor
  @param inner:<float> outer smoothing scale of the structure tensor
  @param coherenceSmooth:<float> sigma for gaussian sm,ooth of the coherene
  @param with_coherence:<bool> switch on/off coherence calculation
  @return tensor,coherence:<ndarray>,<ndarray> 
  """
  coherence = None
  
  assert len(img.shape) != 2
  
  img = img[:,:,0]

  tensor = vigra.filters.structureTensor(img.astype(np.float32), inner, outer)
  if with_coherence:
      coherence = np.sqrt((tensor[:,:,2]-tensor[:,:,0])**2+2*tensor[:,:,1]**2)/(tensor[:,:,2]+tensor[:,:,0]+1e-16)
      if coherenceSmooth > 0:      
        coherence = vigra.filters.gaussianSmoothing(coherence,coherenceSmooth)

  return tensor,coherence



def directionsFromTensor(tensor):
  """
  @summary: Calculates the direction of the smaller eigenvector from the structure tensoor
  @param tensor:<ndarray> structure tensor
  @return directions: <ndarray>  
  """
  shape = [tensor[:,:,0].shape[0],tensor[:,:,0].shape[1]]
  directions = np.zeros((tensor[:,:,0].shape[0],tensor[:,:,0].shape[1],2),dtype=np.float32)
  
  evals = vigra.filters.tensorEigenvalues(tensor)
  evecs1 = np.zeros((shape[0],shape[1],2),dtype=np.float32)
  evecs2 = np.zeros((shape[0],shape[1],2),dtype=np.float32)

  evecs1[:,:,0] = tensor[:,:,1]    
  evecs1[:,:,1] = evals[:,:,0]-tensor[:,:,0]    
  evecs2[:,:,0] = tensor[:,:,1]
  evecs2[:,:,1] = evals[:,:,1]-tensor[:,:,0]

  #call a cython function to get the direction with higher coherence
  cE._chooseEigenVectors(evals,evecs1,evecs2,directions)

  return directions













