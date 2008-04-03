#!/usr/bin/env python

"""
A verification script for mktoc. By default run all test cases and report
all failures. The output of all test input CUE files will be verified
against a set of matching TOC files.
"""

import sys
import os
import unittest
import mktoc

CUE_DIR = './cue'
TOC_DIR = './toc'

class IntegrationTest(unittest.TestCase):

   if not os.path.exists(CUE_DIR): os.mkdir(CUE_DIR)
   if not os.path.exists(TOC_DIR): os.mkdir(TOC_DIR)
   cues = [c for c in os.listdir(CUE_DIR) if os.path.splitext(c)[1] == '.cue']
   tocs = [ os.path.splitext(f)[0] + '.toc' for f in cues]

   def setUp(self):
      self.cue_file = self.cues.pop(0)
      self.toc_file = self.tocs.pop(0)
      self.create_toc_file()

   def testCueFile01(self): self.check_file()
   def testCueFile02(self): self.check_file()
   def testCueFile03(self): self.check_file()
   def testCueFile04(self): self.check_file()
   def testCueFile05(self): self.check_file()
   def testCueFile06(self): self.check_file()
   def testCueFile07(self): self.check_file()
   def testCueFile08(self): self.check_file()
   def testCueFile09(self): self.check_file()
   def testCueFile10(self): self.check_file()
   def testCueFile11(self): self.check_file()
   def testCueFile12(self): self.check_file()
   def testCueFile13(self): self.check_file()
   def testCueFile14(self): self.check_file()
   def testCueFile15(self): self.check_file()
   def testCueFile16(self): self.check_file()
   def testCueFile17(self): self.check_file()
   def testCueFile18(self): self.check_file()
   def testCueFile19(self): self.check_file()
   def testCueFile20(self): self.check_file()
   def testCueFile21(self): self.check_file()
   def testCueFile22(self): self.check_file()
   def testCueFile23(self): self.check_file()
   def testCueFile24(self): self.check_file()
   def testCueFile25(self): self.check_file()
   def testCueFile26(self): self.check_file()
   def testCueFile27(self): self.check_file()
   def testCueFile28(self): self.check_file()
   def testCueFile29(self): self.check_file()
   def testCueFile30(self): self.check_file()
   def testCueFile31(self): self.check_file()
   def testCueFile32(self): self.check_file()
   def testCueFile33(self): self.check_file()
   def testCueFile34(self): self.check_file()
   def testCueFile35(self): self.check_file()
   def testCueFile36(self): self.check_file()
   def testCueFile37(self): self.check_file()
   def testCueFile38(self): self.check_file()
   def testCueFile39(self): self.check_file()
   def testCueFile40(self): self.check_file()
   def testCueFile41(self): self.check_file()
   def testCueFile42(self): self.check_file()
   def testCueFile43(self): self.check_file()
   def testCueFile44(self): self.check_file()
   def testCueFile45(self): self.check_file()
   def testCueFile46(self): self.check_file()
   def testCueFile47(self): self.check_file()
   def testCueFile48(self): self.check_file()
#   def testCueFile49(self): self.check_file()
#   def testCueFile50(self): self.check_file()

   def create_toc_file(self):
      toc_path = os.path.join(TOC_DIR,self.toc_file)
      if not os.path.exists(toc_path):
         cue_fh = open(os.path.join(CUE_DIR,self.cue_file))
         toc_fh = open(toc_path,'w')
         toc_str = mktoc.CueParser(cue_fh, find_wav=False).get_toc()
         # write the data
         toc_fh.write( toc_str.read() )
         cue_fh.close()
         toc_fh.close()

   def check_file(self):
      # calculate test data
      cue_fh = open(os.path.join(CUE_DIR,self.cue_file))
      toc_fh = mktoc.CueParser(cue_fh, find_wav=False).get_toc()
      cue_fh.close()
      toc = [s for s in toc_fh.readlines()]
      toc_fh.close()
      # read the known good data
      toc_good_fh = open(os.path.join(TOC_DIR,self.toc_file))
      toc_good = [s for s in toc_good_fh.readlines()]
      toc_good_fh.close()
      # compare data sets
      if toc != toc_good:
         for a,b in zip(toc,toc_good):
            err_str = "strings do not match\n  %s:%s\n  %s:%s" % \
                        (self.cue_file,repr(a),self.toc_file,repr(b))
            self.assertEqual(a,b,err_str)


class TrackTimeTest(unittest.TestCase):
   """Verify Index classs."""
   def testIndex(self):
      """Time object string output must be equal to the input string."""
      tlist = ['00:01:02','99:98:97']
      for i in tlist:
         val = str(mktoc.TrackTime(i))
         self.assertEqual(val,i)

   def testEquals(self):
      """Time object must be equal to each other."""
      a = mktoc.TrackTime('01:02:03')
      b = mktoc.TrackTime('01:02:03')
      self.assertEqual( a, b )

   def testNotEquals(self):
      """Time object must be equal to each other."""
      a = mktoc.TrackTime('01:20:03')
      b = mktoc.TrackTime('01:02:03')
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
      a = mktoc.TrackTime('00:00:00')
      b = mktoc.TrackTime('00:00:01')
      self.assertRaises( mktoc.CueUnderflowError, mktoc.TrackTime.__sub__, a, b )

   def time_sub(self,s):
      self.assertEqual( str(mktoc.TrackTime(s[0]) - mktoc.TrackTime(s[1])), \
                        str(mktoc.TrackTime(s[2])) )

if __name__ == '__main__':
   unittest.main()

