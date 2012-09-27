from ilastik.applets.base.applet import Applet

from opObjectFeatures import OpObjectFeatures
from objectFeaturesGui import ObjectFeaturesGui
#FIXME: do a serializer later
#from objectExtractionSerializer import ObjectExtractionSerializer

from lazyflow.graph import OperatorWrapper

class ObjectFeaturesApplet( Applet ):
    def __init__( self, graph, guiName="Object Features", projectFileGroupName="ObjectFeatures" ):
        
        super(ObjectFeaturesApplet, self).__init__( guiName )
        self._topLevelOperator = OperatorWrapper(OpObjectFeatures, graph=graph)

        self._gui = ObjectFeaturesGui(self._topLevelOperator)
        
        #self._serializableItems = [ ObjectExtractionSerializer(self._topLevelOperator, projectFileGroupName) ]
        self._serializableItems = []
        
    @property
    def topLevelOperator(self):
        return self._topLevelOperator

    @property
    def dataSerializers(self):
        return self._serializableItems

    @property
    def viewerControlWidget(self):
        return self._centralWidget.viewerControlWidget

    @property
    def gui(self):
        return self._gui