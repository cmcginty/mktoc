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
Unit testing framework for mktoc_wav module.
"""

__date__    = '$Date$'
__version__ = '$Revision$'

import os
import sys
import unittest
import inspect

from mktoc.base import *
from mktoc.wav  import *


class WavFileCacheTests(unittest.TestCase):
   """Unit tests for the external interface of the WavFileCache class. These
   test rely on predifined file names in test directory."""
   _WAV_DIR = 'test_data/wav_names'

   def __init__(self, *args, **kwargs):
      """Initialize the test case data directory."""
      super(WavFileCacheTests,self).__init__(*args, **kwargs)
      # get the directory location of this module, and update the
      # location of the test data dirs
      file_dir = os.path.dirname(inspect.getfile(sys._getframe()))
      self._WAV_DIR = os.path.join(file_dir,self._WAV_DIR)

   def testNoMatch(self):
      """A file that can not be found in the test dir must through an
      exception."""
      wc = WavFileCache(self._WAV_DIR)
      self.assertRaises( FileNotFoundError, wc.lookup, 'not a file')

   def testExactMatch(self):
      """A source name with an exact match in the test dir must be found."""
      wc = WavFileCache(self._WAV_DIR)
      self.assertTrue( wc.lookup('My Test File-1.wav'))

   def testSubDirSrcMatch(self):
      """A source name with a pre-appended sub-dir to an exact match in the
      test dir must be found."""
      wc = WavFileCache(self._WAV_DIR)
      self.assertTrue( wc.lookup('./dir2/My Test File-1.wav'))

   def testSubDirDestMatch(self):
      """A name with an exact match in a sub-dir of the test dir must be
      found."""
      wc = WavFileCache(self._WAV_DIR)
      self.assertTrue( wc.lookup('My Test File In A Dir-1.wav'))

   def testSubDirReverseMatch(self):
      """A source name with a pre-appended DOS path sub-dir to an exact match
      in the test dir must be found."""
      wc = WavFileCache(self._WAV_DIR)
      self.assertTrue( wc.lookup('C:\dir1\dir2\My Test File-1.wav'))

   def testUnderlineAsSpaceMatch(self):
      """A source name with underscores instead of spaces must be found in the
      test dir."""
      wc = WavFileCache(self._WAV_DIR)
      self.assertTrue( wc.lookup('My_Test_File-1.wav'))

   def testSpaceAsUnderlinesMatch(self):
      """A source name with spaces instead of underscores must be found in the
      test dir."""
      wc = WavFileCache(self._WAV_DIR)
      self.assertTrue( wc.lookup('My Test File-2.wav'))

##############################################################################
if __name__ == '__main__':
   """Execute all test cases define in this file."""
   unittest.main()

