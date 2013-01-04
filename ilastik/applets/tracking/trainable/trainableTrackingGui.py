from PyQt4 import uic

import os
import math
import logging
import numpy as np
import pgmlink

from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
from volumina.layer import ColortableLayer
from volumina.pixelpipeline.datasourcefactories import createDataSource
from volumina import colortables


logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)

class TrainableTrackingGui( LayerViewerGui ):
    def __init__( self, topLevelOperatorView, additionalMonitoredSlots=[]):
        super(TrainableTrackingGui, self).__init__(topLevelOperatorView, additionalMonitoredSlots)
        self._collected = []

    def setupLayers( self ):
        layers = []
        if self.topLevelOperatorView.LabelImage.ready():
            layer = ColortableLayer( createDataSource(self.topLevelOperatorView.LabelImage),
                                     colortables.create_random_16bit() )
            layers.append( layer )
        return layers

    def handleEditorRightClick( self, position5d, globalWindowCoordinate ):
        sl = [slice(c,c+1,None) for c in position5d]
        clicked_label = self.topLevelOperatorView.LabelImage(sl).wait()[0,0,0,0,0]
        # label at timestep 
        self._collect( clicked_label, position5d[0] )

    # overriden from LayerViewerGui
    def initAppletDrawerUi( self ):
        localDir = os.path.split(__file__)[0]
        self._drawer = uic.loadUi(localDir+"/drawer.ui")
        self._drawer.pushButton.pressed.connect(self._onButtonPressed)

    def _onButtonPressed( self ):
        print "Do it!"
        g = self.topLevelOperatorView.graphEditor.graph
        print "graph stats:"
        print "nodes:", pgmlink.countNodes(g)  ,"arcs:", pgmlink.countArcs(g)

    def _collect( self, label, at_timestep ):
        #background
        if label == 0:
            return

        l = len(self._collected)
        if l == 0:
            self._collected.append( (label, at_timestep) )
        elif l == 1 and (at_timestep - self._collected[0][1])==1 :
            self._collected.append( (label, at_timestep) )            
            self.topLevelOperatorView.graphEditor.addMove( self._collected[0], self._collected[1] )
            self._collected = []
        
        assert(len(self._collected) < 4)
