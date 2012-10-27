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
    
    def __init__(self, operator):
        super(LightfieldGui2, self).__init__()
        uic.loadUi(self.CENTRAL_WIDGET_PATH,self)
        
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    gui = LightfieldGui2(None)
#    gui.show()