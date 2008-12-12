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

__date__    = '$Date$'
__version__ = '$Revision$'

import sys
sys.path.insert(0,'src')  # allow setup.py to import mktoc.base

import os
from distutils.core import setup

import mktoc
from mktoc.base import *

def _read( *path_name ):
   return open( os.path.join(os.path.dirname(__file__), *path_name)).read()

long_doc = mktoc.__doc__ + '\n' + _read('INSTALL.txt')

setup( name='mktoc',
       version=VERSION,
       description="""\
          Simple command line tool to create TOC files for CD burning with
          cdrdao.""",
       long_description=long_doc,
       author=__author__,
       author_email=__email__,
       url='http://mktoc.googlecode.com',
       download_url=(
          'http://mktoc.googlecode.com/files/mktoc-%s.tar.gz' % (VERSION,)),
       packages=['mktoc'],
       package_dir = {'':'src'},
       scripts=['scripts/mktoc'],
       classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Environment :: Console',
          'Intended Audience :: End Users/Desktop',
          'License :: OSI Approved :: GNU General Public License (GPL)',
          'Operating System :: OS Independent',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python',
          'Topic :: Multimedia :: Sound/Audio :: CD Audio :: CD Writing',
          'Topic :: Multimedia :: Sound/Audio :: Conversion',
         ]
      )

