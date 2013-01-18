'''
Created on Oct 14, 2012

@author: fredo
'''
from lazyflow.graph import OperatorWrapper
from ilastik.applets.base.standardApplet import StandardApplet
from lightfieldOperator import LightfieldOperator

class LightfieldApplet( StandardApplet ):
    """
    This is a simple viewer applet
    """
    def __init__( self, projectFileGroupName, workflow ):
#        self._topLevelOperator = LightfieldOperator(parent = workflow)
        super(LightfieldApplet, self).__init__(projectFileGroupName, workflow)

        self._topLevelOperator = OperatorWrapper( LightfieldOperator, graph=workflow.graph, promotedSlotNames=set(['InputImage']) )
        
        self._preferencesManager = None
        self._serializableItems = []
#        self._gui = None

    
    @property
    def singleLaneGuiClass(self):
        from lightfieldGui import LightfieldGui
        return LightfieldGui
    
    @property
    def singleLaneOperatorClass(self):
        return LightfieldOperator
    
    @property
    def broadcastingSlots(self):
#        return ["outerScale", "innerScale"]
#        return ["InputImage"]
        return []
    
    @property
    def dataSerializers(self):
        return self._serializableItems

#    @property
#    def topLevelOperator(self):
#        return self._topLevelOperator
    
    @property
    def appletPreferencesManager(self):
        return self._preferencesManager
    
#    def getMultiLaneGui( self ):
#        if self._gui is None:
#            from lightfieldGui import LightfieldGui
#            self._gui = LightfieldGui( self.topLevelOperator)
#        return self._gui