'''
Created on Oct 27, 2012

@author: fredo
'''

from ilastik.applets.base.applet import Applet
from lightfieldGui2 import LightfieldGui2


class LightfieldApplet2(Applet):
    
    def __init__(self,graph):
        super(LightfieldApplet2, self).__init__("lightfield panel")
        self._topLevelOperator = None
#        self._topLevelOperator = OperatorWrapper( OpLayerViewer, graph=graph, promotedSlotNames=set(['RawInput']) )
        self._preferencesManager = None
        self._serializableItems = []
        self._gui = None
    
    @property    
    def gui(self):
        if self._gui is None:        
            self._gui = LightfieldGui2( self.topLevelOperator )
        return self._gui
    
    @property
    def dataSerializers(self):
        return self._serializableItems

    @property
    def topLevelOperator(self):
        return self._topLevelOperator
    
    @property
    def appletPreferencesManager(self):
        return self._preferencesManager