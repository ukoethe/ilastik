'''
Created on Oct 11, 2012

@author: fredo
'''

from ilastik.shell.gui.startShellGui import startShellGui
from lightfieldWorkflow import LightfieldWorkflow
import os

DEBUG = True
TEST_PROJECT_PATH = os.path.join(os.path.dirname(__file__),"test-project.ilp")

if __name__ == "__main__":
    if DEBUG:
        def test(shell):
            shell.openProjectFile(TEST_PROJECT_PATH)
        
        startShellGui( LightfieldWorkflow, test)
    else:
        startShellGui(LightfieldWorkflow)