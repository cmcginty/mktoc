#!/usr/bin/env python

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
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Unit test framework script to test a set of modules in a single step. The
script uses the modules defined in the 'mod_to_test' variable to load for
testing.
"""

__date__    = '$Date$'
__version__ = '$Revision$'

import unittest
import logging

# enable line below to turn on logging
# logging.basicConfig(level=logging.DEBUG)

# defines modules to be tested
mod_to_test = [ 'mktoc.test_disc',
                'mktoc.test_parser',
                'mktoc.test_wav',
                'mktoc.test_progress_bar']

def suite():
   """Unit test init function to return a TestSuite structure of all test
   contained in the defined modules."""
   # create TestSuite object
   alltests = unittest.TestSuite()
   # load all modules define in the module list
   for name in mod_to_test:
      mod = __import__(name)        # import module or package
      components = name.split('.')
      for comp in components[1:]:   # load remaining items
         mod = getattr(mod,comp)
      alltests.addTest(unittest.findTestCases(mod))
   return alltests

if __name__ == '__main__':
   unittest.main(defaultTest='suite')

