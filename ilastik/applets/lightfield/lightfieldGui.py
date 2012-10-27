'''
Created on Oct 14, 2012

@author: fredo
'''
from ilastik.applets.layerViewer.layerViewerGui import LayerViewerGui
from volumina.pixelpipeline.imagepump import ImagePump
from volumina.slicingtools import SliceProjection, SliceProjectionTest
from volumina.eventswitch import EventSwitch
from volumina.navigationControler import NavigationControler, NavigationInterpreter
from volumina.brushingcontroler import BrushingControler, BrushingInterpreter, CrosshairControler
from volumina.clickReportingInterpreter import ClickReportingInterpreter
from PyQt4.QtGui import QTransform,QWidget
from PyQt4 import uic
import os
useVTK = True

import logging

try:
    from volumina.view3d.view3d import OverviewScene
except:
    print "Warning: could not import optional dependency VTK"
    useVTK = False

class LightfieldGui(LayerViewerGui):
    
    APPLET_DRAWER_PATH = os.path.join(os.path.dirname(__file__),"drawer.ui")
    logger = logging.getLogger(__name__)
    
    def __init__(self, toplevelOperator):
        super(LightfieldGui,self).__init__(toplevelOperator)
        #=======================================================================
        # rearrange views
        #=======================================================================
        x_slicing_view = self.volumeEditorWidget.quadview.splitHorizontal1.widget(1)
        y_slicing_view = self.volumeEditorWidget.quadview.splitHorizontal2.widget(0)
        z_slicing_view = self.volumeEditorWidget.quadview.splitHorizontal1.widget(0)
        view_3d = self.volumeEditorWidget.quadview.splitHorizontal2.widget(1)
        
        self.volumeEditorWidget.quadview.splitHorizontal1.addWidget(x_slicing_view)
        self.volumeEditorWidget.quadview.splitHorizontal1.addWidget(y_slicing_view)
        self.volumeEditorWidget.quadview.splitHorizontal1.addWidget(z_slicing_view)
        self.volumeEditorWidget.quadview.splitHorizontal2.addWidget(view_3d)
        
        self.initDrawers()
        
        
    def initDrawers(self):
        self._drawers = uic.loadUi(self.APPLET_DRAWER_PATH)
        
        self._drawers.editChannelSubmit.clicked.connect(self.editChannel)
        self._drawers.editGaussSubmit.clicked.connect(self.editGauss)
        
    def appletDrawers(self):
        return [("Lightfield View", self._drawers )]
    
    def editGauss(self):
        self.logger.info("Edit Gauss has been clicked.")
    
    def editChannel(self):
        self.logger.info("Edit channel has been clicked")
        
