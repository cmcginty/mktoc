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
Unit testing framework for mktoc.cmdline module.
"""

__date__    = '$Date$'
__version__ = '$Revision$'

import unittest
from mock import patch
from contextlib import nested

from mktoc.cmdline import *
from mktoc.base import *

class TestCmdLine( unittest.TestCase):

   _FILE_NAME = '/tmp/mktoc.txt'

   def setUp(self):
      self.cl = CommandLine()

   def testFileOpenUtf8(self):
      fh = self.cl._open_file( self._FILE_NAME,'wb')
      fh.write( u'\xf1' )
      fh.close()

      fh = self.cl._open_file( self._FILE_NAME )
      line = fh.read()
      fh.close()
      self.assertTrue( line == u'\xf1' )

   def testParseError(self):
      """Verify that ParseError exception is caught and handled."""
      with nested (
            patch.object(CommandLine, '_run'),
            patch.object(CommandLine, '_error_msg')
            ) as (run_method, err_method):
         # throw a parseError
         run_method.side_effect = ParseError('message')
         self.cl.run()
         self.assertEquals( err_method.call_count, 1 )
         # the execption was passed to the err_method
         self.assertEquals( err_method.call_args[0][0],
                            run_method.side_effect )

