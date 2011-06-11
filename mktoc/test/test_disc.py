#  Copyright (c) 2011, Patrick C. McGinty
#
#  This program is free software: you can redistribute it and/or modify it
#  under the terms of the Simplified BSD License.
#
#  See LICENSE text for more details.
"""
   Unit testing framework for mktoc_disc module.
"""

__date__    = '$Date$'
__version__ = '$Revision$'

import unittest

from mktoc.base import *
from mktoc.disc import *
from mktoc.disc import _TrackTime


##############################################################################
class TrackTimeTests(unittest.TestCase):
   """Unit tests for the external interface of the TrackTime class."""
   def testIndex(self):
      """Time object string output must be equal to the input string."""
      tlist = ['00:01:02','99:98:97']
      for i in tlist:
         val = str(_TrackTime(i))
         self.assertEqual(val,i)

   def testEquals(self):
      """Time object must be equal to each other."""
      a = _TrackTime('01:02:03')
      b = _TrackTime('01:02:03')
      self.assertEqual( a, b )

   def testNotEquals(self):
      """Time object must not be equal to each other."""
      a = _TrackTime('01:20:03')
      b = _TrackTime('01:02:03')
      self.failIfEqual( a, b )

   def testSubtractionOfSelf(self):
      """Time object must subtract correctly."""
      self.time_sub(['10:10:10','10:10:10','00:00:00'])

   def testSubtractionMin(self):
      """Time object must subtract correctly."""
      self.time_sub(['10:10:10','01:00:00','09:10:10'])

   def testSubtractionSec(self):
      """Time object must subtract correctly."""
      self.time_sub(['10:10:10','00:01:00','10:09:10'])

   def testSubtractionFrame(self):
      """Time object must subtract correctly."""
      self.time_sub(['10:10:10','00:00:01','10:10:09'])

   def testSubtractionSecUF(self):
      """Time object must subtract correctly."""
      self.time_sub(['10:10:10','00:11:00','09:59:10'])

   def testSubtractionFrameUF(self):
      """Time object must subtract correctly."""
      self.time_sub(['10:10:10','00:00:11','10:09:74'])

   def testSubtractionUF(self):
      """Time object must raise exception if subtract underflows."""
      a = _TrackTime('00:00:00')
      b = _TrackTime('00:00:01')
      self.assertRaises( UnderflowError, _TrackTime.__sub__, a, b )

   def time_sub(self,s):
      """Helper function for test cases above."""
      self.assertEqual( str(_TrackTime(s[0]) - _TrackTime(s[1])), \
                        str(_TrackTime(s[2])) )


##############################################################################
if __name__ == '__main__':
   """Execute all test cases define in this file."""
   unittest.main()

