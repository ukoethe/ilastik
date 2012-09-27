from PyQt4.QtGui import *
from PyQt4 import uic

from igms.featureTableWidget import FeatureEntry
from igms.featureDlg import FeatureDlg

import os
import numpy
from ilastik.utility import bind
from lazyflow.operators import OpSubRegion

import logging
logger = logging.getLogger(__name__)
traceLogger = logging.getLogger('TRACE.' + __name__)

from lazyflow.tracer import traceLogged
from ilastik.applets.layerViewer import LayerViewerGui

import volumina.colortables as colortables
from volumina.api import LazyflowSource, GrayscaleLayer, ColortableLayer

class ObjectFeaturesGui(LayerViewerGui):
    
    def appletDrawers(self):
        return [ ("Object features", self.drawer ) ]

    def viewerControlWidget(self):
        return self._viewerControlWidget
    
    @traceLogged(traceLogger)
    def __init__(self, mainOperator):
        """
        """
        super(ObjectFeaturesGui, self).__init__([ mainOperator.BinaryImage, mainOperator.LabeledImage, mainOperator.InputImage ])
        self.mainOperator = mainOperator

    
    @traceLogged(traceLogger)
    def initAppletDrawerUi(self):
        """
        Load the ui file for the applet drawer, which we own.
        """
        localDir = os.path.split(__file__)[0]
        # (We don't pass self here because we keep the drawer ui in a separate object.)
        self.drawer = uic.loadUi(localDir+"/drawer.ui")
        self.drawer.labelImageButton.clicked.connect(self.onLabelImageButtonClicked)
        self.drawer.extractObjectsButton.clicked.connect(self.onExtractObjectsButtonClicked)
        
    @traceLogged(traceLogger)
    def setupLayers(self, currentImageIndex):
        
        layers = []
        
        inputSlot = self.mainOperator.InputImage[currentImageIndex]
        binarySlot = self.mainOperator.BinaryImage[currentImageIndex]
        labeledSlot = self.mainOperator.LabeledImage[currentImageIndex]
        
        if inputSlot.ready():
            inputLayer = self.createStandardLayerFromSlot( inputSlot )
            inputLayer.name = "Input Data"
            inputLayer.visible = True
            inputLayer.opacity = 1.0
            layers.append(inputLayer)
        
        if binarySlot.ready():
            ct = colortables.create_default_8bit()
            self.binaryimagesrc = LazyflowSource( self.mainOperator.BinaryImage )
            layer = GrayscaleLayer( self.binaryimagesrc, range=(0,1), normalize=(0,1) )
            layer.name = "Binary Image"
            layer.visible = True
            layer.opacity = 1.0
            #self.layerstack.append(layer)
            layers.append(layer)

        if labeledSlot.ready():
            ct = colortables.create_default_16bit()
            self.objectssrc = LazyflowSource( self.mainOperator.LabelImage )
            ct[0] = QColor(0,0,0,0).rgba() # make 0 transparent
            layer = ColortableLayer( self.objectssrc, ct )
            layer.name = "Label Image"
            layer.opacity = 0.5
            layer.visible = True
            #self.layerstack.append(layer)
            layers.append(layer)
            
        return layers
    
    @traceLogged(traceLogger)
    def onLabelImageButtonClicked(self):
        print "clicked the label image button!"
        
    @traceLogged(traceLogger)
    def onExtractObjectsButtonClicked(self):
        print "clicked the extract objects button!"