'''
Created on Oct 27, 2012

@author: fredo
'''
from lazyflow.graph import Operator,InputSlot, OutputSlot
import logging
import NativeUtil as operations

class LightfieldOperator(Operator):
    """
    @author: Frederik Claus
    @summary: Performs various operations on a lightfield
    """
    Operation = InputSlot()
    Options = InputSlot()
    InputImage = InputSlot()
    
    Output = OutputSlot()
    
    logger = logging.getLogger(__name__)
    
    def setupOutputs(self):
        self.Output.meta.assignFrom(self.InputImage.meta)
        
    def execute(self, slot, subindex, roi, result):
        key = roi.toSlice()
        raw = self.InputImage[key].wait()
        #get the channel we are supposed to work on
        channel = key[-1].start
        
        worker = self.Operation.value
        args = self.Options.value
        
        self.dispatch(worker,args,raw,channel)
        result[...] = raw
    
    def propagateDirty(self, slot, subindex, roi):
        if slot.name == "InputImage":
            self.Output.setDirty(roi)
        elif slot.name == "Options" or slot.name == "Operation":
            self.Output.setDirty( slice(None) )
        else:
            self.logger.error("Unknown slot name %s." % slot.name)            
        
    def dispatch(self,operation,args,raw,channel):
        operation = operation.lower()
        if not hasattr(operations, operation):
            raise RuntimeError, "Can not dispatch to %s. No such function." % operation
        self.logger.info("Dispatching to %s with %s on channel %d" % (operation,args,channel))
        op = getattr(operations,operation)
        op(raw,channel,**args)
        