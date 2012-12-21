from PyQt4 import uic

import os
import math

import logging
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
from volumina.layer import ColortableLayer
from volumina.pixelpipeline.datasourcefactories import createDataSource
from volumina import colortables
import numpy as np

logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)


class TrainableTrackingGui( LayerViewerGui ):
    def __init__( self, *args, **kwargs ):
        super(LayerViewerGui, self).__init__(*args, **kwargs)
        self._collected = []

    def setupLayers( self ):
        layers = []
        if self.topLevelOperatorView.LabelImage.ready():
            layer = ColortableLayer( createDataSource(self.topLevelOperatorView.LabelImage),
                                     colortables.create_random_16bit() )
            layers.append( layer )
        return layers

    def handleEditorRightClick( self, position5d, globalWindowCoordinate ):
        print "yatta!", position5d, globalWindowCoordinate
        sl = [slice(c,c+1,None) for c in position5d]
        clicked_label = self.topLevelOperatorView.LabelImage(sl).wait()
        print clicked_label
        self._collect( label )

    def _collect( self, label ):
        self._collected.append( clicked_label )
