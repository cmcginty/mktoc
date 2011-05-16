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
Unit testing framework for mktoc_paraser module.
"""

__date__    = '$Date$'
__version__ = '$Revision$'

import sys
import os
import inspect
import unittest

from mktoc.base import *
from mktoc.parser import *
from mktoc.disc import *


class CueParserFileTests(unittest.TestCase):
   """Unit tests for the external interface of the CueParser class. These test
   rely on predefined input and output files. If the input CUE file does not
   match the expected output TOC file, the test will fail."""
   _CUE_DIR = 'data/cue'
   _TOC_DIR = 'data/toc'
   _cue_list   = []
   _toc_list   = []

   def __init__(self, *args, **kwargs):
      """Initialize the test case by creating any missing sub-dirs and
      generating the starting list of CUE and TOC files to use for the test
      cases."""
      super(CueParserFileTests,self).__init__(*args, **kwargs)

      # get the directory location of this module, and update the
      # location of the test data dirs
      file_dir = os.path.dirname(inspect.getfile(sys._getframe()))
      self._CUE_DIR = os.path.join(file_dir,self._CUE_DIR)
      self._TOC_DIR = os.path.join(file_dir,self._TOC_DIR)

      # on first init, generate a list of cue files
      if not len(self._cue_list):
         if not os.path.exists(self._CUE_DIR): os.mkdir(self._CUE_DIR)
         if not os.path.exists(self._TOC_DIR): os.mkdir(self._TOC_DIR)
         # create a list of CUE files in the test directory
         cues = [c for c in os.listdir(self._CUE_DIR) if \
                        os.path.splitext(c)[1] == '.cue']
         tocs = [ os.path.splitext(f)[0] + '.toc' for f in cues]
         self._cue_list.extend( cues )
         self._toc_list.extend( tocs )

   def setUp(self):
      """Setup each test case by updating the CUE and TOC files to be used for
      the next test case. If the TOC file does not exist, it will be
      created."""
      self._cue_file = self._cue_list.pop(0)
      self._toc_file = self._toc_list.pop(0)
      self._create_toc_file()

   def testCueFile01(self): self._check_file()
   def testCueFile02(self): self._check_file()
   def testCueFile03(self): self._check_file()
   def testCueFile04(self): self._check_file()
   def testCueFile05(self): self._check_file()
   def testCueFile06(self): self._check_file()
   def testCueFile07(self): self._check_file()
   def testCueFile08(self): self._check_file()
   def testCueFile09(self): self._check_file()
   def testCueFile10(self): self._check_file()
   def testCueFile11(self): self._check_file()
   def testCueFile12(self): self._check_file()
   def testCueFile13(self): self._check_file()
   def testCueFile14(self): self._check_file()
   def testCueFile15(self): self._check_file()
   def testCueFile16(self): self._check_file()
   def testCueFile17(self): self._check_file()
   def testCueFile18(self): self._check_file()
   def testCueFile19(self): self._check_file()
   def testCueFile20(self): self._check_file()
   def testCueFile21(self): self._check_file()
   def testCueFile22(self): self._check_file()
   def testCueFile23(self): self._check_file()
   def testCueFile24(self): self._check_file()
   def testCueFile25(self): self._check_file()
   def testCueFile26(self): self._check_file()
   def testCueFile27(self): self._check_file()
   def testCueFile28(self): self._check_file()
   def testCueFile29(self): self._check_file()
   def testCueFile30(self): self._check_file()
   def testCueFile31(self): self._check_file()
   def testCueFile32(self): self._check_file()
   def testCueFile33(self): self._check_file()
   def testCueFile34(self): self._check_file()
   def testCueFile35(self): self._check_file()
   def testCueFile36(self): self._check_file()
   def testCueFile37(self): self._check_file()
   def testCueFile38(self): self._check_file()
   def testCueFile39(self): self._check_file()
   def testCueFile40(self): self._check_file()
   def testCueFile41(self): self._check_file()
   def testCueFile42(self): self._check_file()
   def testCueFile43(self): self._check_file()
   def testCueFile44(self): self._check_file()
   def testCueFile45(self): self._check_file()
   def testCueFile46(self): self._check_file()
   def testCueFile47(self): self._check_file()
   def testCueFile48(self): self._check_file()
#   def testCueFile49(self): self._check_file()
#   def testCueFile50(self): self._check_file()

   def _create_toc_file(self):
      """Use the CueParser class to create a new TOC file from the currently
      selected CUE file."""
      toc_path = os.path.join(self._TOC_DIR,self._toc_file)
      if not os.path.exists(toc_path):
         cue_fh = open(os.path.join(self._CUE_DIR,self._cue_file))
         toc_fh = open(toc_path,'w')
         toc_str = CueParser( find_wav=False).parse( cue_fh).getToc()
         # write the data
         toc_fh.write( toc_str.read() )
         cue_fh.close()
         toc_fh.close()

   def _check_file(self):
      """The primary test code of this set is defined here. Its job is to
      exercise the CueParser class, and verify the output data with known good
      TOC file data."""
      # calculate test data
      cue_fh = open(os.path.join(self._CUE_DIR,self._cue_file))
      toc = CueParser( find_wav=False).parse( cue_fh).getToc()
      cue_fh.close()
      # read the known good data
      toc_good = open(os.path.join(self._TOC_DIR,self._toc_file))
      # compare data sets
      if toc != toc_good:
         for a,b in map(None,toc,toc_good):
            err_str = "strings do not match\n  %s:%s\n  %s:%s" % \
                        (self._cue_file,repr(a),self._toc_file,repr(b))
            self.assertEqual(a,b[:-1],err_str)
      toc_good.close()


class CueParserTests(unittest.TestCase):
   """Basic unit test for CueParser class."""
   def testParseDisc_BadLine(self):
     cp = CueParser()
     cp._cue = ['BAD MATCH LINE']
     cp._track_lines = [1]    # ignore lines after _cue[1]
     self.assertRaisesRegexp(
           ParseError, ".+: '%s'" % (cp._cue[0]), cp._parse_disc )

   def testParseTrack_BadLine(self):
     cp = CueParser()
     cp._cue = ['SKIP','BAD MATCH LINE']
     cp._track_lines = [1]    # ignore lines before _cue[0]
     cp._file_lines = [(0,'file1')]  # cached file lines/names
     self.assertRaisesRegexp(
           ParseError, ".+: '%s'" % (cp._cue[1],),
           cp._parse_track, 0, Disc())


class WavParserTests(unittest.TestCase):
   def testWavFiles(self):
      """WavParser class must instantiate without errors."""
      wav_list = ['unique-1.wav','unique-2.wav','unique-3.wav']
      parser = WavParser( find_wav=False)
      data = parser.parse( wav_list )
      self.assertTrue( parser )
      self.assertTrue( data )


if __name__ == '__main__':
   """Execute all test cases define in this file."""
   unittest.main()

