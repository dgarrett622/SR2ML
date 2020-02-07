#_________________________________________________________________
#
#
#_________________________________________________________________
"""
Created on Feb. 4, 2020
@author: wangc, mandd
"""

from __future__ import absolute_import

from .ExponentialModel import ExponentialModel
from .ErlangianModel import ErlangianModel
from .GammaModel import GammaModel
from .Factory import knownTypes
from .Factory import returnInstance
from .Factory import returnClass

__all__ = ['ExponentialModel',
          'ErlangianModel',
          'GammaModel']
