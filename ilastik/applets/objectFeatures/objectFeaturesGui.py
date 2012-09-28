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
        super(ObjectFeaturesGui, self).__init__( mainOperator )
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
    def initViewerControlUi(self):
        self._viewerControlWidget = uic.loadUi(os.path.split(__file__)[0] + "/viewerControls.ui")
        layerListWidget = self._viewerControlWidget.listWidget

        # Need to handle data changes because the layerstack model hasn't 
        # updated his data yet by the time he calls the rowsInserted signal
        def handleLayerStackDataChanged(startIndex, stopIndex):
            row = startIndex.row()
            layerListWidget.item(row).setText(self.layerstack[row].name)
        self.layerstack.dataChanged.connect(handleLayerStackDataChanged)
        
        def handleInsertedLayers(parent, start, end):
            for i in range(start, end+1):
                layerListWidget.insertItem(i, self.layerstack[i].name)
        self.layerstack.rowsInserted.connect( handleInsertedLayers )

        def handleRemovedLayers(parent, start, end):
            for i in range(start, end+1):
                layerListWidget.takeItem(i)
        self.layerstack.rowsRemoved.connect( handleRemovedLayers )
        
        def handleSelectionChanged(row):
            # Only one layer is visible at a time
            print "selection changed"
            for i, layer in enumerate(self.layerstack):
                layer.visible = (i == row)
        layerListWidget.currentRowChanged.connect( handleSelectionChanged )
    
    @traceLogged(traceLogger)
    def setupLayers(self, currentImageIndex):
        
        layers = []
        
        inputSlot = self.mainOperator.InputImage[currentImageIndex]
        #binarySlot = self.mainOperator.BinaryImage[currentImageIndex]
        labeledSlot = self.mainOperator.LabeledImage[currentImageIndex]
        
        if inputSlot.ready():
            inputLayer = self.createStandardLayerFromSlot( inputSlot )
            inputLayer.name = "Input Data"
            inputLayer.visible = True
            inputLayer.opacity = 1.0
            layers.append(inputLayer)
        '''
        if binarySlot.ready():
            ct = colortables.create_default_8bit()
            self.binaryimagesrc = LazyflowSource( self.mainOperator.BinaryImage )
            layer = GrayscaleLayer( self.binaryimagesrc, range=(0,1), normalize=(0,1) )
            layer.name = "Binary Image"
            layer.visible = True
            layer.opacity = 1.0
            #self.layerstack.append(layer)
            layers.append(layer)
        '''
            
        if labeledSlot.ready():
            ct = colortables.create_default_16bit()
            self.objectssrc = LazyflowSource( labeledSlot )
            ct[0] = QColor(0,0,0,0).rgba() # make 0 transparent
            layer = ColortableLayer( self.objectssrc, ct )
            layer.name = "Labeled Image"
            layer.opacity = 0.5
            layer.visible = True
            #self.layerstack.append(layer)
            layers.append(layer)
            
        return layers
    
    def onLabelImageButtonClicked(self):
        print "clicked the label image button!"
        self.mainOperator.inputs["OutputPath"].setValue("/home/akreshuk/data/3dcube_cc.h5/volume/data")
        
    def onExtractObjectsButtonClicked(self):
        print "clicked the extract objects button!"