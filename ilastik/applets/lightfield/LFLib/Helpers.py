import os
import h5py as h5
import numpy as np
from types import StringType

def splitPath(s):
  """
  @author: Sven Wanner  
  @brief: takes an absolute path and returns the filename as first, the 
  filetype as second and the location of the file as third result
  @param s: <string> path 
  @return data,filetype,path
  """
  print "incoming path",s
  path = s
  while s.find("/") != -1:
      res = s.split("/")
      s = res[2]
  data = res[len(res)-1]
  filetype = data.partition(".")[2]
  data = data.partition(".")[0]
  return data,filetype,path.partition(data)[0]


def changeKey(d,old_key,new_key):
  """
  @author: Sven Wanner  
  @brief: change the key name of a dictionary key
  @param old_key: <string> old key name 
  @param new_key: <string> new key name
  """
  if type(d) is dict:
    d[new_key] = d.pop(old_key)
  else:
    print "WARNING!!! Error in changeKey!"
    
    
def ensure_dir_from_current(f):
  """
  @author: Sven Wanner  
  @brief: checks if input dir exist relative to the calling module location, if not it will be created and returned 
  @param f: <string> directory 
  @return d: <string> path
  """
  cwd = os.getcwd()
  d = os.path.dirname(cwd+f)
  if not os.path.exists(d):
    os.makedirs(d)
  return d
  
def ensure_dir(f):
  """
  @author: Sven Wanner  
  @brief: checks if input dir exist, if not it will be created and returned 
  @param f: <string> directory 
  @return d: <string> path 
  """  
  if type(f) is StringType: 
    if f[-1] != "/":
      f+="/"
    d = os.path.dirname(f); print d
    if not os.path.exists(d):
      os.makedirs(d)
    return d
  else:
    print "Error: ensure_dir needs a string argument!"
    return None
  
  
def createH5(datasets=[],attrs=[],location="./",name="file.h5"):
  """
  @author: Sven Wanner 
  @brief: creates a h5 file from input datasets and attributes
  @param dataset: <list> list of dictionaries-> [{"name":"dataset_name","data":ndarray,:"dtype":dtype}, ... ]
  @param attrs: <list> list of dictionaries -> [{"name":attrs_name,"value":value}, ...]
  @param location: <string>  save location 
  @param name: <string> save name
  """
  if location is not None:
    if location[-1] != "/":
      print "add a slash to location!"
      location += "/"
    print "location in createH5",location
    loc = ensure_dir(location)+"/"
    if name.find(".h5") == -1:
      name+=".h5"
    
    location = loc+name
    print "try to write h5 file at: loc =",location+name,"results in location",location
    
    f = h5.File(location, 'w')
    for d in datasets:
      f.create_dataset(d["name"], data=d["data"], dtype=d["dtype"], compression='gzip')
    for a in attrs:
      f.attrs[a["name"]] = a["value"]
    f.close()
    

def readH5(infile):
  """
  @author: Sven Wanner 
  @brief: reads a h5 file from input file string and returns lists of datasets and attributes
  @param dataset: <list> list of dictionaries -> [{"name":"dataset_name","data":ndarray,:"dtype":dtype}, ... ]
  @param attrs: <list> list of dictionaries -> [{"name":attrs_name,"value":value}, ...]
  @return dsets,ats: <dictionary> dsets  of ndarrays {"name":data,....}; ats [dictionary] of attributes {"name":value,....}
  """
  f = h5.File(infile, 'r')
  datasets = list(f)
  attrs = list(f.attrs)
  
  dsets = {}
  ats = {}
  for d in datasets:
    dsets[str(d)] = np.copy(f[str(d)])
  for a in attrs:
    ats[str(a)] = f.attrs[str(a)]
    
  return dsets,ats
  
  
  
def aopen(infile, string, line=0, out = None):
  """
  @author: Sven Wanner 
  @brief: opens a file and appends some content without deleting the former content. 
  @param infile: <string> filename
  @param line: <int> position of content to append 
  @param string: <string> content to append 
  @param out: <string> outfilename, if None, the infilename is chosen
  """
  try:
    f = open(infile, 'r').readlines()
    a = f[:line]
    b = f[line:]
    a.append(string)
    if out is None:
      out = infile
      open(out, 'w').write(''.join(a + b))
  except Exception as e:
    print "\nException in aopen!"
    print e,"\n"
  
  
  
    
    