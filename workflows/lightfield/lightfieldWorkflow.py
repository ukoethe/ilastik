from ilastik.workflow import Workflow

from lazyflow.graph import Graph

from ilastik.applets.dataSelection import DataSelectionApplet

from ilastik.applets.lightfield.lighfieldApplet import LightfieldApplet
from ilastik.applets.lightfield.lightfieldApplet2 import LightfieldApplet2

class LightfieldWorkflow(Workflow):
    def __init__(self):
        super(LightfieldWorkflow, self).__init__()
        self._applets = []

        # Create a graph to be shared by all operators
        graph = Graph()

        # Create applets 
        self.dataSelectionApplet = DataSelectionApplet(graph, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
        self.viewerApplet = LightfieldApplet(graph)
        self.lightfieldApplet = LightfieldApplet2(graph)

        self._applets.append( self.dataSelectionApplet )
        self._applets.append( self.viewerApplet )
#        self._applets.append( self.lightfieldApplet )
        
        # Connect top-level operators
        self.viewerApplet.topLevelOperator.RawInput.connect( self.dataSelectionApplet.topLevelOperator.Image )

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName
