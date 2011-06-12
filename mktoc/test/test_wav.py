#  Copyright (c) 2011, Patrick C. McGinty
#
#  This program is free software: you can redistribute it and/or modify it
#  under the terms of the Simplified BSD License.
#
#  See LICENSE text for more details.
"""
   Unit testing framework for mktoc_wav module.
"""

import os
import sys
import unittest
import inspect

from mktoc.base import *
from mktoc.wav  import *
from mktoc import progress_bar as mt_pb


##############################################################################
class WavFileCacheTests(unittest.TestCase):
   """Unit tests for the external interface of the WavFileCache class. These
   test rely on predifined file names in test directory."""
   _WAV_DIR = 'data/wav_names'

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
      self.assertRaises( FileNotFoundError, wc, 'not a file')

   def testExactMatch(self):
      """A source name with an exact match in the test dir must be found."""
      wc = WavFileCache(self._WAV_DIR)
      self.assertTrue( wc('My Test File-1.wav'))

   def testWhiteSpaceMatch(self):
      """A source name with extra white space added to an exact match in the
      test dir must be found."""
      wc = WavFileCache(self._WAV_DIR)
      self.assertTrue( wc('  My Test File-1.wav  '))

   def testSubDirSrcMatch(self):
      """A source name with a pre-appended sub-dir to an exact match in the
      test dir must be found."""
      wc = WavFileCache(self._WAV_DIR)
      self.assertTrue( wc('./dir2/My Test File-1.wav'))

   def testSubDirDestMatch(self):
      """A name with an exact match in a sub-dir of the test dir must be
      found."""
      wc = WavFileCache(self._WAV_DIR)
      self.assertTrue( wc('My Test File In A Dir-1.wav'))

   def testSubDirReverseMatch(self):
      """A source name with a pre-appended DOS path sub-dir to an exact match
      in the test dir must be found."""
      wc = WavFileCache(self._WAV_DIR)
      self.assertTrue( wc('C:\dir1\dir2\My Test File-1.wav'))

   def testUnderlineAsSpaceMatch(self):
      """A source name with underscores instead of spaces must be found in the
      test dir."""
      wc = WavFileCache(self._WAV_DIR)
      self.assertTrue( wc('My_Test_File-1.wav'))

   def testSpaceAsUnderlinesMatch(self):
      """A source name with spaces instead of underscores must be found in the
      test dir."""
      wc = WavFileCache(self._WAV_DIR)
      self.assertTrue( wc('My Test File-2.wav'))

   def testMatchAsLeadSubstr(self):
      """A source name matches a substring of a file in the test dir."""
      wc = WavFileCache(self._WAV_DIR)
      self.assertTrue( wc('Text My Test File-3.wav'))

   def testMatchAsTrailSubstr(self):
      """A source name matches a substring of a file in the test dir."""
      wc = WavFileCache(self._WAV_DIR)
      self.assertTrue( wc('My Test File-3 Trail.wav'))

   def testFailMatchAsNSubstr(self):
      """A source name matches a substring of multiple files in the test dir
      should raise an exception."""
      wc = WavFileCache(self._WAV_DIR)
      self.assertRaises( TooManyFilesMatchError, wc, 'My Test File-3.wav')

   def testUnicodeFileNameMatch(self):
      """A unicode file should be matched correctly."""
      wc = WavFileCache()
      wc._data = [u'/\xf1']
      self.assertTrue( wc(u'\xf1'))


##############################################################################
class WavOffsetWriterTest(unittest.TestCase):
   """Unit tests for the external interface of the WavOffsetWriter class."""
   def testInitClass(self):
      """WavOffsetWriter class must initialize correctly."""
      wow = WavOffsetWriter(10, mt_pb.ProgressBar, ('test message',))
      self.assertTrue(wow)


##############################################################################
if __name__ == '__main__':
   """Execute all test cases define in this file."""
   unittest.main()

