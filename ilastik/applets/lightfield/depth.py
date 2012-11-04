'''
Created on Oct 30, 2012

@author: fredo
'''

dirty = False
lf = None
#
#class DepthManager:
#    """ A python singleton """
#
#    
    
#class DepthManager():
#    
#    _instance = None
#    
#    def __new__(cls, *args, **kwargs):
#        if not cls._instance:
#            cls._instance = super(DepthManager, cls).__new__(
#                                cls, *args, **kwargs)
#            cls._instance.dirty = False
#            cls._instance.depth = None
#        return cls._instance
#    
##    def __init__(self):
##        if hasattr(self,"dirty"):
##            return
##        self.dirty = False
##        self.depth = None
#    
#    

if __name__ == "__main__":
    manager1 = DepthManager()
    manager1.dirty = True
    print manager1.dirty
    
    manager2 = DepthManager()
    print manager2.dirty
    print manager2 == manager1