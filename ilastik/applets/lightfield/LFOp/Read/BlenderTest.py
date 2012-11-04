'''
Created on Sep 17, 2012

@author: fredo
'''

from Blender import ReadBlenderOperator
from LFOp.OperatorTestCase import OperatorTestCase
from LFOp import settings
import unittest

class ReadBlenderOperatorTest(OperatorTestCase):
  
  OPERATOR = ReadBlenderOperator
  
  def testSingleRow(self):
    self.op.inDir.setValue(settings.TEST_384x25_PATH)
    self.op.inChannel.setValue(3)
    self.useAndAssertOutLf(None, origShape = (1,25,384,384,3))
    self.op.inChannel.setValue(1)
    self.useAndAssertOutLf(None, origShape = (1,25,384,384,1))
    
    
if __name__ == "__main__":
  unittest.main()