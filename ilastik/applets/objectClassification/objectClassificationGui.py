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
from volumina.api import LazyflowSource, GrayscaleLayer, ColortableLayer, AlphaModulatedLayer

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
        labelSlots.labelOutput = pipeline.LabelOutputs  
        #labelSlots.labelEraserValue = pipeline.opLabelArray.eraser
        #labelSlots.labelDelete = pipeline.opLabelArray.deleteLabel
        labelSlots.maxLabelValue = pipeline.MaxLabelValue
        labelSlots.labelsAllowed = pipeline.LabelsAllowedFlags
        labelSlots.maxObjectNumber = pipeline.MaxObjectNumber
        labelSlots.labelEraserValue.setValue(100)
        labelSlots.labelDelete.setValue(-1)
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
        
        self.clickedObjects = dict() #maps from object to the label that is used for it
        self.usedLabels = set()

    '''
    @traceLogged(traceLogger)
    def initEditor(self):
        super(ObjectClassificationGui, self).initEditor()
        
        #Change brushing for picking
        self.pickingModel = PickingModel()
        self.pickingControler = PickingControler(self.pickingModel, self.editor.posModel, None)
        self.pickingInterpreter = PickingInterpreter(self.editor.navCtrl, self.pickingControler)
        
        
        #self.editor.brushingControler = self.pickingControler
        #self.editor.brushingInterpreter = self.pickingInterpreter
        #self.editor.brushingModel = self.pickingModel
    '''
    
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
    
    @traceLogged(traceLogger)
    def createLabelLayer():
        self, currentImageIndex, direct=False):
        """
        Return a colortable layer that displays the label slot data, along with its associated label source.
        direct: whether this layer is drawn synchronously by volumina
        """
        labelOutput = self._labelingSlots.labelOutput[currentImageIndex]
        if not labelOutput.ready():
            return (None, None)
        else:
            traceLogger.debug("Setting up labels for image index={}".format(currentImageIndex) )
            # Add the layer to draw the labels, but don't add any labels
            labelsrc = RelabelingLazyflowSinkSource( self._labelingSlots.labelOutput[currentImageIndex],
                                           self._labelingSlots.labelInput[currentImageIndex])
        
           
            relabeling=numpy.zeros(self.maxObjectNumber+1, dtype=a.dtype), colortable=colortable, direct=direct)
            labellayer = ClickableColortableLayer(self.editor, self.onClick, source=labelsrc, colortable=self._colorTable16, \
                                             relabeling=relabeling, direct=direct)
       
            #labellayer = ColortableLayer(labelsrc, colorTable = self._colorTable16, direct=direct )
            labellayer.name = "Labels"
            labellayer.ref_object = None
            
            return labellayer, labelsrc
    
    
    @traceLogged(traceLogger)
    def setupLayers(self, currentImageIndex):
        
        # Base class provides the label layer.
        print "AAAAAAAAAAAAAAAAAAAa, setupLayers of the objectClassificationGui"
        layers = super(ObjectClassificationGui, self).setupLayers(currentImageIndex)
        #print "AAAAAAAAAAAAAAAAAAAa, setupLayers of the objectClassificationGui"
        #This is just for colors
        labels = self.labelListData
        
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
        # Add each of the predictions
        for channel, predictionSlot in enumerate(self.pipeline.PredictionProbabilityChannels[currentImageIndex]):
            if predictionSlot.ready() and channel < len(labels):
                ref_label = labels[channel]
                predictsrc = LazyflowSource(predictionSlot)
                predictLayer = AlphaModulatedLayer( predictsrc,
                                                    tintColor=ref_label.color,
                                                    range=(0.0, 1.0),
                                                    normalize=(0.0, 1.0) )
                predictLayer.opacity = 0.25
                predictLayer.visible = self.labelingDrawerUi.checkInteractive.isChecked()
                predictLayer.visibleChanged.connect(self.updateShowPredictionCheckbox)

                def setLayerColor(c):
                    predictLayer.tintColor = c
                def setLayerName(n):
                    newName = "Prediction for %s" % ref_label.name
                    predictLayer.name = newName
                setLayerName(ref_label.name)

                ref_label.colorChanged.connect(setLayerColor)
                ref_label.nameChanged.connect(setLayerName)
                layers.append(predictLayer)
            
        
            inputLayer = self.createStandardLayerFromSlot( inputSlot )
            inputLayer.name = "Input Data"
            inputLayer.visible = True
            inputLayer.opacity = 1.0
            layers.append(inputLayer)
        '''
        return layers
    
    @pyqtSlot()
    @traceLogged(traceLogger)
    def handleLabelSelectionChange(self):
        enabled = False
        if self.pipeline.MaxLabelValue.ready():
            enabled = True
            enabled &= self.pipeline.MaxLabelValue.value >= 2
            #enabled &= numpy.prod(self.pipeline.CachedFeatureImages[self.imageIndex].meta.shape) > 0
        
        self.labelingDrawerUi.savePredictionsButton.setEnabled(enabled)
        self.labelingDrawerUi.checkInteractive.setEnabled(enabled)
        self.labelingDrawerUi.checkShowPredictions.setEnabled(enabled)
        
    def toggleInteractive(self, checked):
        print "Interactive mode toggled to", checked
        
    def onClick(layer, pos5D, pos):
        #FIXME: this should label in the selected label color
        obj = layer.data.originalData[pos5D]
        if obj in self.clickedObjects:
            layer._datasources[0].setRelabelingEntry(obj, 0)
            usedLabels.remove( self.clickedObjects[obj] )
            del clickedObjects[obj]
        else:
            labels = sorted(list(self.usedLabels))
            
            #find first free entry
            if labels:
                for l in range(1, labels[-1]+2):
                    if l not in labels:
                        break
                assert l not in self.usedLabels
            else:
                l = 1
            
            num = self.editor.brushingModel.drawnNumber
            self.usedLabels.add(l) 
            self.clickedObjects[obj] = l
            layer._datasources[0].setRelabelingEntry(obj, num)
        
        