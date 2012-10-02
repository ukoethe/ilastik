from PyQt4.QtGui import *
from PyQt4 import uic
from PyQt4.QtCore import pyqtSlot

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
from ilastik.applets.labeling import LabelingGui

import volumina.colortables as colortables
from volumina.api import LazyflowSource, GrayscaleLayer, ColortableLayer

from pickingControler import PickingInterpreter, PickingControler
from pickingModel import PickingModel

class ObjectClassificationGui(LabelingGui):
    
    def centralWidget( self ):
        return self
    
    def appletDrawers(self):
        # Get the labeling drawer from the base class
        labelingDrawer = super(ObjectClassificationGui, self).appletDrawers()[0][1]
        return [ ("Training", labelingDrawer) ]
        
        #return [ ("Object picking", self.drawer ) ]
    
    def reset(self):
        # Base class first
        super(ObjectClassificationGui, self).reset()

        # Ensure that we are NOT in interactive mode
        self.labelingDrawerUi.checkInteractive.setChecked(False)
        self.labelingDrawerUi.checkShowPredictions.setChecked(False)
        
    @traceLogged(traceLogger)
    def __init__(self, pipeline, guiControlSignal, shellRequestSignal ):
        # Tell our base class which slots to monitor
        labelSlots = LabelingGui.LabelingSlots()
        labelSlots.labelInput = pipeline.LabelInputs
        labelSlots.labelOutput = pipeline.LabelImages
        labelSlots.labelEraserValue = pipeline.opLabelArray.eraser
        labelSlots.labelDelete = pipeline.opLabelArray.deleteLabel
        labelSlots.maxLabelValue = pipeline.MaxLabelValue
        labelSlots.labelsAllowed = pipeline.LabelsAllowedFlags

        # We provide our own UI file (which adds an extra control for interactive mode)
        # This UI file is copied from pixelClassification pipeline
        # 
        labelingDrawerUiPath = os.path.split(__file__)[0] + '/labelingDrawer.ui'
        
        # Base class init
        super(ObjectClassificationGui, self).__init__( labelSlots, pipeline, labelingDrawerUiPath)
        
        self.pipeline = pipeline
        self.guiControlSignal = guiControlSignal
        self.shellRequestSignal = shellRequestSignal
        
        #self.predictionSerializer = predictionSerializer
        
        self.interactiveModeActive = False
        #self._currentlySavingPredictions = False

        self.labelingDrawerUi.checkInteractive.setEnabled(True)
        self.labelingDrawerUi.checkInteractive.toggled.connect(self.toggleInteractive)
        #self.labelingDrawerUi.labelImageButton.clicked.connect(self.onLabelImageButtonClicked)
        #self.labelingDrawerUi.extractObjectsButton.clicked.connect(self.onExtractObjectsButtonClicked)
        #self.labelingDrawerUi.savePredictionsButton.clicked.connect(self.onSavePredictionsButtonClicked)

        #self.labelingDrawerUi.checkShowPredictions.clicked.connect(self.handleShowPredictionsClicked)
        #def nextCheckState():
        #    if not self.labelingDrawerUi.checkShowPredictions.isChecked():
        #        self.labelingDrawerUi.checkShowPredictions.setChecked(True)
        #    else:
        #        self.labelingDrawerUi.checkShowPredictions.setChecked(False)
        #self.labelingDrawerUi.checkShowPredictions.nextCheckState = nextCheckState
        
        self.pipeline.MaxLabelValue.notifyDirty( bind(self.handleLabelSelectionChange) )

    
    @traceLogged(traceLogger)
    def initEditor(self):
        super(ObjectClassificationGui, self).initEditor()
        
        #Change brushing for picking
        self.pickingModel = PickingModel()
        self.pickingControler = PickingControler(self.pickingModel, self.editor.posModel, None)
        self.pickingInterpreter = PickingInterpreter(self.editor.navCtrl, self.pickingControler)
        
        
        self.editor.brushingControler = self.pickingControler
        self.editor.brushingInterpreter = self.pickingInterpreter
        self.editor.brushingModel = self.pickingModel
    
    
    @traceLogged(traceLogger)
    def initAppletDrawerUi(self):
        """
        Load the ui file for the applet drawer, which we own.
        """
        localDir = os.path.split(__file__)[0]
        # (We don't pass self here because we keep the drawer ui in a separate object.)
        self.drawer = uic.loadUi(localDir+"/drawer.ui")
        #self.drawer.labelImageButton.clicked.connect(self.onLabelImageButtonClicked)
        #self.drawer.extractObjectsButton.clicked.connect(self.onExtractObjectsButtonClicked)
        
    '''
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
    '''
    @traceLogged(traceLogger)
    def setupLayers(self, currentImageIndex):
        
        # Base class provides the label layer.
        layers = super(ObjectClassificationGui, self).setupLayers(currentImageIndex)
        
        inputSlot = self.pipeline.InputImages[currentImageIndex]
        #binarySlot = self.mainOperator.BinaryImage[currentImageIndex]
        #labeledSlot = self.pipeline.ConnCompImages[currentImageIndex]
        
        if inputSlot.ready():
            print "setting up layers in objectClass gui"
            ct = colortables.create_default_16bit()
            print "Input slot type:", inputSlot.meta
            self.objectssrc = LazyflowSource( inputSlot )
            ct[0] = QColor(0,0,0,0).rgba() # make 0 transparent
            layer = ColortableLayer( self.objectssrc, ct )
            layer.name = "Connected Components"
            layer.opacity = 0.5
            layer.visible = True
            #self.layerstack.append(layer)
            layers.append(layer)
            
        '''
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
            self.objectssrc = LazyflowSource( labeledSlot )
            ct[0] = QColor(0,0,0,0).rgba() # make 0 transparent
            layer = ColortableLayer( self.objectssrc, ct )
            layer.name = "Connected Components"
            layer.opacity = 0.5
            layer.visible = True
            #self.layerstack.append(layer)
            layers.append(layer)
        else:
            print "conn comp slot not ready"
        '''
        return layers
    
    
    '''
    def onLabelImageButtonClicked(self):
        print "clicked the label image button!"
        #self.pipeline.inputs["OutputPath"].setValue("/home/akreshuk/data/3dcube_cc.h5/volume/data")
        #self.updateAllLayers()
        
    def onExtractObjectsButtonClicked(self):
        print "clicked the extract objects button!"
   ''' 
    @pyqtSlot()
    @traceLogged(traceLogger)
    def handleLabelSelectionChange(self):
        #insert something here, someday
        print "Label changed"
        
    def toggleInteractive(self, checked):
        print "Interactive mode toggled to", checked
        