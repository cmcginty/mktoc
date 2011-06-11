#!/usr/bin/env python

#  Copyright (c) 2011, Patrick C. McGinty
#
#  This program is free software: you can redistribute it and/or modify it
#  under the terms of the Simplified BSD License.
#
#  See LICENSE text for more details.
"""
   Distools setup file for the mktoc application.
"""

__date__    = '$Date$'
__version__ = '$Revision$'

import os
from distutils.core import setup

import mktoc
from mktoc.base import *

def _read( *path_name ):
   return open( os.path.join(os.path.dirname(__file__), *path_name)).read()

long_doc = mktoc.__doc__ + '\n' + _read('INSTALL.rst')

setup( name='mktoc',
       version=VERSION,
       description=
         """Simple command line tool generates TOC files for audio CD burning
         with cdrdao.""",
       long_description=long_doc,
       author=__author__,
       author_email=__email__,
       url='https://github.com/cmcginty/mktoc',
       download_url=(
          'https://github.com/cmcginty/mktoc/blob/master/dist/mktoc-%s.tar.gz'
            % (VERSION,)),
       packages=['mktoc'],
       scripts=['bin/mktoc'],
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

