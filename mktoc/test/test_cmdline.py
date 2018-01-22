#  Copyright (c) 2011, Patrick C. McGinty
#
#  This program is free software: you can redistribute it and/or modify it
#  under the terms of the Simplified BSD License.
#
#  See LICENSE text for more details.
"""
   Unit testing framework for mktoc.cmdline module.
"""

import unittest
from mock import patch

from mktoc.cmdline import *
from mktoc.base import *

class TestCmdLine( unittest.TestCase):

   _FILE_NAME = '/tmp/mktoc.txt'

   def setUp(self):
      self.cl = CommandLine()

   def testFileOpenUtf8(self):
      fh = self.cl._open_file( self._FILE_NAME,'wb','utf-8')
      fh.write( '\xf1' )
      fh.close()

      fh = self.cl._open_file( self._FILE_NAME, encoding='utf-8')
      line = fh.read()
      fh.close()
      self.assertTrue( line == '\xf1' )

   def testParseError(self):
      """Verify that ParseError exception is caught and handled."""
      with patch.object(CommandLine, '_run') as run_method, patch.object(
              CommandLine, '_error_msg') as err_method:
         # throw a parseError
         run_method.side_effect = ParseError('message')
         self.cl.run()
         self.assertEqual( err_method.call_count, 1 )
         # the execption was passed to the err_method
         self.assertEqual( err_method.call_args[0][0],
                            run_method.side_effect )

