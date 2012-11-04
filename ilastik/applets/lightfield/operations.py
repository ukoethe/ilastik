from LFLib.LFDepth.depthFromStructureTensor import DepthFromStructureTensor
from lazyflow.graph import Graph
import numpy as np
import NativeUtil

def depth(lf,inner,outer):
    op = DepthFromStructureTensor(graph = Graph())
    op.inputLF.setValue(lf)
    op.innerScale.setValue(inner)
    op.outerScale.setValue(outer)
    op.colorMode.setValue(0)
    op.coherenceSmooth.setValue(0.8)
    op.sigmaXStrength.setValue(1.0)
    op.maxLabel.setValue(4)
    op.minLabel.setValue(-4)
    op.useThreading.setValue(False)
    oldShape = lf.shape
    lf = op.outputs["outputLF"][:].allocate().wait()
#    newLf = np.zeros(shape = oldShape)
#    NativeUtil.put(lf,newLf)
#    print "got shape %s." % str(newLf.shape)
#    newLf =  lf[:,:,:,:,0:1]
#    print "Old shape: %s, new Shape: %s" % (str(origShape),str(newLf.shape))
    return lf
#    return newLf