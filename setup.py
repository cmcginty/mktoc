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
#  along with this program.  If not, see <http://www.gnu.org/licenses/>

"""
Distools setup file for the mktoc application.
"""
import sys
sys.path.insert(0,'src')  # allow setup.py to import mktoc.base

import os
from distutils.core  import setup
from distutils.command.install_scripts import install_scripts
from mktoc.base import __author__, __email__, __copyright__, __license__
from mktoc.base import __version__

__date__ = '$Date$'

class install_scripts_renamed(install_scripts):
   """Override the stanard install_script class to strip the '.py' extension
   from any script files."""
   def run(self):
      curr_scripts = self.get_inputs()
      for f in [os.path.basename(p) for p in curr_scripts]:
         os.rename(os.path.join(self.build_dir,f), \
                   os.path.join(self.build_dir,os.path.splitext(f)[0]))
      install_scripts.run(self)

setup( name='mktoc', version=__version__,
       description='CD audio CUE file interpretor for cdrdao',
       author=__author__,
       author_email=__email__,
       url='http://mktoc.googlecode.com',
       packages=['mktoc'],
       package_dir = {'':'src'},
       scripts=['src/mktoc.py'],
       cmdclass={'install_scripts':install_scripts_renamed},
      )


