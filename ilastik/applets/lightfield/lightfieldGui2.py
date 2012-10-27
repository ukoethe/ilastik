'''
Created on Oct 27, 2012

@author: fredo
'''

from PyQt4.QtGui import *
from PyQt4 import uic
import os
import sys


class LightfieldGui2(QMainWindow):
    
    CENTRAL_WIDGET_PATH = os.path.join(os.path.dirname(__file__),"centralWidget.ui")
    
    
    def centralWidget( self ):
        """
        Return the widget that will be displayed in the main viewer area.
        """
        return self

    
    def appletDrawers(self):
        """
        Return a list of (drawer title, drawer widget) pairs for this applet.
        """
        return [("Lightfield Control", QWidget())]
    
    
    def menus( self ):
        """
        Return a list of QMenu widgets to be shown in the menu bar when this applet is visible.
        """
        return None


    def viewerControlWidget(self):
        """
        Return the widget that controls how the content of the central widget is displayed.
        Typically this consists of a layer list control.
        """
        return None
    
   
    def setImageIndex(self, imageIndex):
        """
        Called by the shell when the user has switched the input image he wants to view.
        The GUI should respond by updating the content of the central widget.
        """
        pass

     
    def reset(self):
        """
        Called by the shell when the current project has been unloaded.
        The GUI should reset itself to its initial state, whatever that is.
        """
        pass
    
    def __init__(self, operator):
        super(LightfieldGui2, self).__init__()
        uic.loadUi(self.CENTRAL_WIDGET_PATH,self)
        
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    gui = LightfieldGui2(None)
    gui.show()
    app.exec_()
#    gui.show()