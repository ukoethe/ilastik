'''
Created on Oct 11, 2012

@author: fredo
'''

from ilastik.workflow import Workflow
from ilastik.applets.dataSelection import DataSelectionApplet
from ilastik.applets.layerViewer.layerViewerApplet import LayerViewerApplet
from lazyflow.graph import Graph

class LightfieldWorkflow(Workflow):
    
    def __init__(self):
        super(LightfieldWorkflow, self).__init__()
        self._applets = []
    
        # Create a graph to be shared by all operators
        graph = Graph()
    
        # Create applets 
        self.dataSelectionApplet = DataSelectionApplet(graph, "Input Data", "Input Data", supportIlastik05Import=True, batchDataGui=False)
        self.viewerApplet = LayerViewerApplet(graph)
    
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