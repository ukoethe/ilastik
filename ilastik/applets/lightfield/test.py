'''
Created on Dec 1, 2012

@author: fredo
'''
from LFLib.LightField import loadLF
from opDepth import OpCalcDepth
from lazyflow.graph import Graph
from LFOp.View.Simple import ViewSimpleOperator

LF_PATH = "/home/fredo/hiwi/Lfs/buddhaCycles_9x9_rgb.h5"

def main():
    lf = loadLF(LF_PATH)
    lf = lf.lf[:]
    graph = Graph()
    op = OpCalcDepth(graph = graph)
    op.inputLF.setValue(lf)
    op.innerScale.setValue(0.6)
    op.outerScale.setValue(0.8)
    badAss = (slice(0, 1, None), slice(0, 9, None), slice(0, 256, None), slice(384, 385, None), slice(0, 1, None))
#    op.outputLF[badAss].wait()
#    op.outputLF[0:1,0:9,0:256,384:385,0:1].wait()
    lf = op.outputLF[0:1,5:6,387:388,0:256,0:1].wait()
    view = ViewSimpleOperator(graph = graph)
    view.Input.setValue(lf)
    view.Output[:].wait()
    print lf.shape
#    print lf
    
if __name__ == "__main__":
    main()
    
    