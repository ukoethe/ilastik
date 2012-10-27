from ilastik.workflow import Workflow

from lazyflow.graph import Graph

from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.lightfield.lighfieldApplet import LightfieldApplet

class LightfieldWorkflow(Workflow):
    def __init__(self):
        super(LightfieldWorkflow, self).__init__()
        self._applets = []

        # Create a graph to be shared by all operators
        graph = Graph()

        # Create applets 
        self.dataSelectionApplet = DataSelectionApplet(graph, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
        self.viewerApplet = LightfieldApplet(graph)

        self._applets.append( self.dataSelectionApplet )
        self._applets.append( self.viewerApplet )
        
        # Connect top-level operators
        self.viewerApplet.topLevelOperator.RawInput.connect( self.dataSelectionApplet.topLevelOperator.Image )

    @property
    def applets(self):
        return self._applets

    @property
    def imageNameListSlot(self):
        return self.dataSelectionApplet.topLevelOperator.ImageName
