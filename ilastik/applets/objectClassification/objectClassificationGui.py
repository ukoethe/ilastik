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
from volumina.api import LazyflowSource, GrayscaleLayer, ColortableLayer, AlphaModulatedLayer, \
                         RelabelingLazyflowSinkSource, ClickableColortableLayer, RelabelingLazyflowSource

from volumina.brushingcontroler import ClickInterpreter2

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
        #FIXME: it's not yet clear what to do with these 2 slots
        #in principle, the operator does not need to connect to them,
        #everything should be done by the model, operator just gets the list
        #connect to dummy slots for now 
        labelSlots.labelEraserValue = pipeline.Eraser
        labelSlots.labelDelete = pipeline.DeleteLabel
        
        labelSlots.maxLabelValue = pipeline.MaxLabelValue
        labelSlots.labelsAllowed = pipeline.LabelsAllowedFlags
        #labelSlots.maxObjectNumber = pipeline.MaxObjectNumber
        
        self.maxObjectNumber = 19
        
        #labelSlots.labelEraserValue.setValue(100)
        #labelSlots.labelDelete.setValue(-1)
        
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
    def createLabelLayer(self, currentImageIndex, direct=False):
        """
        Return a colortable layer that displays the label slot data, along with its associated label source.
        direct: whether this layer is drawn synchronously by volumina
        """
        print "!!!!!!!!!!!!!!!!! creating label layer"
        labelOutput = self._labelingSlots.labelOutput[currentImageIndex]
        #maxObjectNumber = self._labelingSlots.maxObjectNumber[currentImageIndex]
        
        #if not labelOutput.ready() or not maxObjectNumber.ready():
        if not labelOutput.ready():
            print "nothing ready yet"
            return (None, None)
        else:
            traceLogger.debug("Setting up labels for image index={}".format(currentImageIndex) )
            # Add the layer to draw the labels, but don't add any labels
            print "!!!!!!!!!!!!!!!!!!!!!1", labelOutput.meta.shape
            labelsrc = RelabelingLazyflowSinkSource( labelOutput,
                                           self._labelingSlots.labelInput[currentImageIndex])
        
           
            #relabeling=numpy.zeros(maxObjectNumber.value+1, dtype=numpy.uint32)
            relabeling=numpy.zeros(self.maxObjectNumber+1, dtype=numpy.uint32)
            labelsrc.setRelabeling(relabeling)
            labellayer = ClickableColortableLayer(self.editor, self.onClick, datasource=labelsrc, \
                                                  colorTable=self._colorTable16, direct=direct)
            #labellayer = ColortableLayer(datasource=labelsrc, \
            #                                      colorTable=self._colorTable16, direct=direct)
            #labellayer = ColortableLayer(labelsrc, colorTable = self._colorTable16, direct=direct )
            labellayer.name = "Labels"
            labellayer.ref_object = None
            labellayer.zeroIsTransparent  = False
            labellayer.colortableIsRandom = True
            
            #FIXME = maybe it shouldn't be done here...
            clickInt = ClickInterpreter2(self.editor, labellayer, self.onClick)
            self.editor.brushingInterpreter = clickInt
            
            return labellayer, labelsrc
    
    
    @traceLogged(traceLogger)
    def setupLayers(self, currentImageIndex):
        
        # Base class provides the label layer.
        layers = super(ObjectClassificationGui, self).setupLayers(currentImageIndex)
        #This is just for colors
        labels = self.labelListData
        
        labelOutput = self._labelingSlots.labelOutput[currentImageIndex]
        binarySlot = self.pipeline.BinaryImages[currentImageIndex]
        
        if binarySlot.ready():
            #print "setting up layers in objectClass gui"
            ct = colortables.create_default_8bit()
            self.binaryimagesrc = LazyflowSource( binarySlot )
            layer = GrayscaleLayer( self.binaryimagesrc, range=(0,1), normalize=(0,1) )
            layer.name = "Binary Image"
            layers.append(layer)
            '''
            ct = colortables.create_default_16bit()
            print "Input slot type:", inputSlot.meta.shape
            self.objectssrc = LazyflowSource( inputSlot )
            ct[0] = QColor(0,0,0,0).rgba() # make 0 transparent
            layer = ColortableLayer( self.objectssrc, ct )
            layer.name = "Connected Components"
            layer.opacity = 0.5
            layer.visible = True
            #self.layerstack.append(layer)
            layers.append(layer)
            '''
        
        predictionSlot = self.pipeline.PredictionLabels[currentImageIndex]
        if predictionSlot.ready():
            self.predictsrc = LazyflowSource( predictionSlot )
            self.predictlayer = ColortableLayer( self.predictsrc, colorTable=self._colorTable16)
            self.predictlayer.name = "Prediction"
            self.predictlayer.ref_object = None
            self.predictlayer.visible = self.labelingDrawerUi.checkInteractive.isChecked()
            layers.append(self.predictlayer)
            
        '''    
        if self.pipeline.PredictionLabels.ready() and labelOutput.ready():
            
            self.predictsrc = RelabelingLazyflowSource(labelOutput)
            print "reset prediction labeling to zeros"
            relabeling=numpy.zeros(self.maxObjectNumber+1, dtype=numpy.uint32)
            self.predictsrc.setRelabeling(relabeling)
            #self.predictsrc.setRelabeling(None)
            self.predictlayer = ClickableColortableLayer(self.editor, self.onClick, datasource = self.predictsrc, colorTable=self._colorTable16)
            self.predictlayer.name = "Prediction"
            self.predictlayer.ref_object = None
            self.predictlayer.visible = self.labelingDrawerUi.checkInteractive.isChecked()
            layers.append(self.predictlayer)
        '''
            
        
        
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
        
    @traceLogged(traceLogger)
    def toggleInteractive(self, checked):
        logger.debug("toggling interactive mode to '%r'" % checked)
        print "toggling interactive mode to '%r'" % checked
        if checked==True:
            if len(self.pipeline.ObjectFeatures) == 0:
                self.labelingDrawerUi.checkInteractive.setChecked(False)
                mexBox=QMessageBox()
                mexBox.setText("There are no features selected ")
                mexBox.exec_()
                return

        self.labelingDrawerUi.savePredictionsButton.setEnabled(not checked)
        self.pipeline.FreezePredictions.setValue( not checked )

        # Auto-set the "show predictions" state according to what the user just clicked.
        if checked:
            self.labelingDrawerUi.checkShowPredictions.setChecked( True )
            self.handleShowPredictionsClicked()

        #FIXME FIXME
        if checked:
            self.forceTrainAndPredict()
       

        # If we're changing modes, enable/disable our controls and other applets accordingly
        if self.interactiveModeActive != checked:
            if checked:
                self.labelingDrawerUi.labelListView.allowDelete = False
                self.labelingDrawerUi.AddLabelButton.setEnabled( False )
            else:
                self.labelingDrawerUi.labelListView.allowDelete = True
                self.labelingDrawerUi.AddLabelButton.setEnabled( True )
        self.interactiveModeActive = checked    

    def forceTrainAndPredict(self):
        
        #print "labels set so far:"
        #print self.pipeline.LabelInputs[0].value
        '''
        labels = numpy.zeros((self.maxObjectNumber,), dtype=numpy.uint32)
        labels[0] = 1
        labels[1] = 1
        labels[2]= 2
        labels[-1] = 2
        self.pipeline.LabelInputs[0].setValue(labels)
        '''
        #feats = self.pipeline.ObjectFeatures[0][0].wait()
        #print feats
        #classifier = self.pipeline.Classifier[:].wait()
        #print "classifier returned"
        #print classifier
        
        predictions = self.pipeline.PredictionLabels[0][:].wait()
        #print predictions
        '''
        predictions = predictions[0].squeeze()
        print predictions.shape
        relabeling = list(predictions)
        relabeling[0]=0
        print relabeling
        self.predictsrc.setRelabeling(relabeling)
        '''
        self.predictlayer.visible = True
        
        
        
        
    @pyqtSlot()
    @traceLogged(traceLogger)
    def handleShowPredictionsClicked(self):
        checked = self.labelingDrawerUi.checkShowPredictions.isChecked()
        for layer in self.layerstack:
            if "Prediction" in layer.name:
                layer.visible = checked
        
        # If we're being turned off, turn off live prediction mode, too.
        if not checked and self.labelingDrawerUi.checkInteractive.isChecked():
            self.labelingDrawerUi.checkInteractive.setChecked(False)
            # And hide all segmentation layers
            for layer in self.layerstack:
                if "Segmentation" in layer.name:
                    layer.visible = False
        
        
    def onClick(self, layer, pos5D, pos):
        
        print "click-click"
        
        slicing = (slice(pos5D[0], pos5D[0]+1), slice(pos5D[1],pos5D[1]), slice(pos5D[2],pos5D[2]+1), slice(pos5D[3],pos5D[3]+1), slice(pos5D[4],pos5D[4]+1))
        arr = layer._datasources[0].request(slicing, original=True).wait()
    
        obj= arr[0][0][0][0][0]
        
        if obj==0:
            return
        oldlabel = layer._datasources[0]._relabeling[obj]
        if oldlabel!=0:
            layer._datasources[0].setRelabelingEntry(obj, 0)
        else:
            num = self.editor.brushingModel.drawnNumber
            layer._datasources[0].setRelabelingEntry(obj, num)
            print "labeled object", obj, "as", num
            layer._datasources[0].put()
        