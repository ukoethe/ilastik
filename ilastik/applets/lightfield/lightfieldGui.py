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
from PyQt4.QtGui import QTransform
useVTK = True
try:
    from volumina.view3d.view3d import OverviewScene
except:
    print "Warning: could not import optional dependency VTK"
    useVTK = False

class LightfieldGui(LayerViewerGui):
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
        
