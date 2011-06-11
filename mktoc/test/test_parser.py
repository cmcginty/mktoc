#  Copyright (c) 2011, Patrick C. McGinty
#
#  This program is free software: you can redistribute it and/or modify it
#  under the terms of the Simplified BSD License.
#
#  See LICENSE text for more details.
"""
   Unit testing framework for mktoc_paraser module.
"""

import inspect
import os
import sys
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

   def testCueFile01(self): self._check_file('01.cue')
   def testCueFile02(self): self._check_file('02.cue')
   def testCueFile03(self): self._check_file('03.cue')
   def testCueFile04(self): self._check_file('04.cue')
   def testCueFile05(self): self._check_file('05.cue')
   def testCueFile06(self): self._check_file('06.cue')
   def testCueFile07(self): self._check_file('07.cue')
   def testCueFile08(self): self._check_file('08.cue')
   def testCueFile09(self): self._check_file('09.cue')
   def testCueFile10(self): self._check_file('10.cue')
   def testCueFile11(self): self._check_file('11.cue')
   def testCueFile12(self): self._check_file('12.cue')
   def testCueFile13(self): self._check_file('13.cue')
   def testCueFile14(self): self._check_file('14.cue')
   def testCueFile15(self): self._check_file('15.cue')
   def testCueFile16(self): self._check_file('16.cue')
   def testCueFile17(self): self._check_file('17.cue')
   def testCueFile18(self): self._check_file('18.cue')
   def testCueFile19(self): self._check_file('19.cue')
   def testCueFile20(self): self._check_file('20.cue')
   def testCueFile21(self): self._check_file('21.cue')
   def testCueFile22(self): self._check_file('22.cue')
   def testCueFile23(self): self._check_file('23.cue')
   def testCueFile24(self): self._check_file('24.cue')
   def testCueFile25(self): self._check_file('25.cue')
   def testCueFile26(self): self._check_file('26.cue')
   def testCueFile27(self): self._check_file('27.cue')
   def testCueFile28(self): self._check_file('28.cue')
   def testCueFile29(self): self._check_file('29.cue')
   def testCueFile30(self): self._check_file('30.cue')
   def testCueFile31(self): self._check_file('31.cue')
   def testCueFile32(self): self._check_file('32.cue')
   def testCueFile33(self): self._check_file('33.cue')
   def testCueFile34(self): self._check_file('34.cue')
   def testCueFile35(self): self._check_file('35.cue')
   def testCueFile36(self): self._check_file('36.cue')
   def testCueFile37(self): self._check_file('37.cue')
   def testCueFile38(self): self._check_file('38.cue')
   def testCueFile39(self): self._check_file('39.cue')
   def testCueFile40(self): self._check_file('40.cue')
   def testCueFile41(self): self._check_file('41.cue')
   def testCueFile42(self): self._check_file('42.cue')
   def testCueFile43(self): self._check_file('43.cue')
   def testCueFile44(self): self._check_file('44.cue')
   def testCueFile45(self): self._check_file('45.cue')
   def testCueFile46(self): self._check_file('46.cue')
   def testCueFile47(self): self._check_file('47.cue')
   def testCueFile48(self): self._check_file('48.cue')
   def testCueFile49(self): self._check_file('49.cue')
   def testCueFile50(self): self._check_file('50.cue')

   def _create_toc_file(self):
      """Use the CueParser class to create a new TOC file from the currently
      selected CUE file."""
      toc_path = os.path.join(self._TOC_DIR,self._toc_file)
      if not os.path.exists(toc_path):
         cue_fh = open(os.path.join(self._CUE_DIR,self._cue_file))
         toc_fh = open(toc_path,'wb')
         toc_str = CueParser( find_wav=False,
                              dir_=self._CUE_DIR).parse( cue_fh).getToc()
         # write the data
         for l in toc_str:
            toc_fh.write("%s\n" % l)
         cue_fh.close()
         toc_fh.close()

   def _check_file(self,fname):
      """The primary test code of this set is defined here. Its job is to
      exercise the CueParser class, and verify the output data with known good
      TOC file data."""
      self._cue_file = fname
      self._toc_file = fname.rstrip('cue')+'toc'
      self._create_toc_file()
      # calculate test data
      with open(os.path.join(self._CUE_DIR,self._cue_file)) as cue_fh:
         toc = CueParser( find_wav=False,
                          dir_=self._CUE_DIR).parse( cue_fh).getToc()
         toc = [t+'\n' for t in toc]
      # read the known good data
      with open(os.path.join(self._TOC_DIR,self._toc_file)) as toc_fh:
         toc_good = toc_fh.readlines()
      # compare data sets
      if toc != toc_good:
         for num,(a,b) in enumerate(map(None,toc,toc_good)):
            err_str = "strings do not match\n  %s:%d:%s\n  %s:%d:%s" % \
                        (self._cue_file,num,repr(a),
                         self._toc_file,num,repr(b))
            self.assertEqual(a,b,err_str)


class CueParserTests(unittest.TestCase):
   """Basic unit test for CueParser class."""
   def testParseDisc_BadLine(self):
      cp = CueParser()
      file_ = ['BAD MATCH LINE']
      self.assertRaisesRegexp(
         ParseError, ".+: '%s'" % (file_[0]), cp.parse, file_ )

   def testParseTrack_BadLine(self):
      cp = CueParser(find_wav=False)
      file_ = ['FILE "track1.wav" WAVE',
         'TRACK 01 AUDIO',
         'BAD MATCH LINE',]
      self.assertRaisesRegexp(
         ParseError, ".+: '%s'" % (file_[2],), cp.parse, file_)

   def testNoCueTracks(self):
      cp = CueParser()
      file_ = """REM GENRE Classical
         REM DATE 2003
         REM DISCID 5F0C0E07
         PERFORMER "artist"
         TITLE "album" """.split('\n')
      self.assertRaises( ParseError, cp.parse, file_)

   def testNoCueDiscInfo(self):
      cp = CueParser(find_wav=False)
      file_ = """FILE "track1.wav" WAVE
         TRACK 01 AUDIO
         TITLE "track name"
         PERFORMER "artist"
         INDEX 00 08:08:18""".split('\n')
      self.assertTrue( cp.parse(file_) )

   def testIgnoreRemCmd(self):
      cp = CueParser(find_wav=False)
      file_ = """REM COMMENT some unknown comment
         REM GENRE Rock
         REM a general comment
         FILE "track1.wav" WAVE
         TRACK 01 AUDIO""".split('\n')
      self.assertTrue( cp.parse(file_) )


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

