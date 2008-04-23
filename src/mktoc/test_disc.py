#  Copyright 2008, Patrick C. McGinty

#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>

"""
Unit testing framework for mktoc_disc module.
"""
import unittest
from mktoc_global import __author__, __email__, __copyright__, __license__
from mktoc_disc import *

__date__ = '$Date$'

class TrackTimeTests(unittest.TestCase):
   """Unit tests for the external interface of the TrackTime class."""
   def testIndex(self):
      """Time object string output must be equal to the input string."""
      tlist = ['00:01:02','99:98:97']
      for i in tlist:
         val = str(TrackTime(i))
         self.assertEqual(val,i)

   def testEquals(self):
      """Time object must be equal to each other."""
      a = TrackTime('01:02:03')
      b = TrackTime('01:02:03')
      self.assertEqual( a, b )

   def testNotEquals(self):
      """Time object must not be equal to each other."""
      a = TrackTime('01:20:03')
      b = TrackTime('01:02:03')
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
      a = TrackTime('00:00:00')
      b = TrackTime('00:00:01')
      self.assertRaises( UnderflowError, TrackTime.__sub__, a, b )

   def time_sub(self,s):
      """Helper function for test cases above."""
      self.assertEqual( str(TrackTime(s[0]) - TrackTime(s[1])), \
                        str(TrackTime(s[2])) )


##############################################################################
if __name__ == '__main__':
   """Execute all test cases define in this file."""
   unittest.main()

