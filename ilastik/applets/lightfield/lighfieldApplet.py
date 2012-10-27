'''
Created on Oct 14, 2012

@author: fredo
'''
from lazyflow.graph import OperatorWrapper
from ilastik.applets.base.applet import Applet
from ilastik.applets.layerViewer.opLayerViewer import OpLayerViewer

class LightfieldApplet( Applet ):
    """
    This is a simple viewer applet
    """
    def __init__( self, graph ):
        super(LightfieldApplet, self).__init__("layer Viewer")

        self._topLevelOperator = OperatorWrapper( OpLayerViewer, graph=graph, promotedSlotNames=set(['RawInput']) )
        self._preferencesManager = None
        self._serializableItems = []
        self._gui = None
    
    @property    
    def gui(self):
        if self._gui is None:
            from lightfieldGui import LightfieldGui            
            self._gui = LightfieldGui( self.topLevelOperator )
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