'''
Created on Sep 12, 2012

@author: fredo
'''

import exceptions
class IllegalArgumentException(exceptions.Exception):
  def __init__(self,args=None):
      self.args = args
