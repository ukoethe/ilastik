#make the program quit on Ctrl+C
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

import os , string
#force QT4 toolkit for the enthought traits UI
os.environ['ETS_TOOLKIT'] = 'qt4'

hasTraits = False
try:
  from enthought.traits.api import Enum, Bool, Float, Int, String, on_trait_change,  Button, String, List
  from enthought.traits.ui.api import Item, View, Group, Action, EnumEditor
  from enthought.traits.api import HasTraits
  hasTraits = True
except:
  from traits.api import Enum, Bool, Float, Int, String, on_trait_change, Button, String, List
  from traitsui.api import Item, View, Group, Action, EnumEditor 
  from traits.api import HasTraits
  hasTraits = True

from PyQt4.QtGui import QApplication, QSplashScreen, QPixmap
from PyQt4 import QtCore

QtCore.QString = str

from ilastikshell.ilastikShell import IlastikShell

from applets.seededWatershed import SeededWatershedApplet
from applets.projectMetadata import ProjectMetadataApplet
from applets.dataSelection import DataSelectionApplet
#from applets.featureSelection import FeatureSelectionApplet
from lazyflow.graph import Graph

app = QApplication([])

# Splash Screen
splashImage = QPixmap("../ilastik-splash.png")
splashScreen = QSplashScreen(splashImage)
splashScreen.show()


# Create a graph to be shared among all the applets
graph = Graph()

# Create the applets for our workflow
projectMetadataApplet = ProjectMetadataApplet()
dataSelectionApplet = DataSelectionApplet(graph, "DataSelection")
#featureSelectionApplet = FeatureSelectionApplet(graph)
segApplet = SeededWatershedApplet(graph)

# Get handles to each of the applet top-level operators
opData = dataSelectionApplet.topLevelOperator
opSegmentor = segApplet.topLevelOperator

# Connect the operators together
# opFeatures.InputImages.connect( opData.Images )
opSegmentor.image.connect( opData.Image )

shell = IlastikShell()
shell.addApplet(projectMetadataApplet)
shell.addApplet(dataSelectionApplet)

shell.addApplet(segApplet)
shell.show()

# Hide the splash screen
splashScreen.finish(shell)

def test():
    from functools import partial
    
    # Open a test project
    shell.openProjectFile('/home/cstraehl/ilastik06-seg-denk.ilp')
    
    # Select a drawer
    shell.setSelectedAppletDrawer( 3 )
    
    # Check the 'interactive mode' checkbox.                               sip api 2 QStringList
    #QTimer.singleShot( 2000, partial(pcApplet.centralWidget._labelControlUi.checkInteractive.setChecked, True) )


# Run a test
#QTimer.singleShot(1, test )
#test()

app.exec_()
