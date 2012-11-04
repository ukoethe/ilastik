'''
Created on Oct 27, 2012

@author: fredo
'''
from lazyflow.graph import Operator,InputSlot, OutputSlot
import depth
import logging
import NativeUtil as nativeOperations
import operations

class LightfieldOperator(Operator):
    """
    @author: Frederik Claus
    @summary: Performs various operations on a lightfield
    """
    Operation = InputSlot(stype = "string")
    Options = InputSlot(stype = "string" )
    InputImage = InputSlot()
    
    Output = OutputSlot()
    
    logger = logging.getLogger(__name__)
    
    def setupOutputs(self):
        operation = self.Operation.value.lower()
        
#        if operation == "depth":
#            shapeLF = self.InputImage.meta.shape
#            shape = (shapeLF[0],shapeLF[1],shapeLF[2],shapeLF[3],2)
#            self.logger.info("Setting shape from %s to %s" % (str(shapeLF),str(shape)))
#            self.Output.meta.shape = shape
#        else:
        self.Output.meta.assignFrom(self.InputImage.meta)
        
    def execute(self, slot, subindex, roi, result):
        key = roi.toSlice()
        raw = self.InputImage[key].wait()        
        operation = self.Operation.value.lower()
        options = self.Options.value
        
        if operation == "depth":
            if True:
                self.logger.info("Building depth...")
                raw = self.InputImage[:].wait()
                raw = operations.depth(raw,**options)
                depth.lf = raw
                depth.dirty = False
            else:
                self.logger.info("Depth already built")
                raw = depth.lf[roi.toSlice()]
#            roi.setDim(4,0,3)
#            origShape = raw.shape
#            raw = self.InputImage[roi.toSlice()].wait()
#            raw = operations.depth(raw,origShape,**options)
        elif operation == "pass":
            pass
        else:
            #get the channel we are supposed to work on
            channel = key[-1].start
            self.dispatch(operation,options,raw,channel)
            
        result[...] = raw
    
    def propagateDirty(self, slot, subindex, roi):
        if slot.name == "InputImage":
            self.Output.setDirty(roi)
        elif slot.name == "Options" or slot.name == "Operation":
            self.Output.setDirty( slice(None) )
        else:
            self.logger.error("Unknown slot name %s." % slot.name)            
        
    def dispatch(self,operation,args,raw,channel):
        if hasattr(nativeOperations, operation):
            op = getattr(nativeOperations,operation)
            self.logger.info("Dispatching to %s with %s" % (operation, operations))
            op(raw,channel,**args)
        else:
            raise RuntimeError, "Can not dispatch to %s. No such function." % operation
         

        
        
        