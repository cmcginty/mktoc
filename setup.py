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

import os
from setuptools import setup
from textwrap import dedent

import mktoc
from mktoc.base import *

def _read( *path_name ):
   return open( os.path.join(os.path.dirname(__file__), *path_name)).read()

long_doc = dedent(mktoc.__doc__)

setup(
   name='mktoc',
   version=VERSION,
   description= 'Simple command line tool generates TOC files '
                'for audio CD burning with cdrdao.',
   long_description=long_doc,
   author=__author__,
   author_email=__email__,
   url='http://packages.python.org/mktoc/',
   download_url=(
      'https://github.com/cmcginty/mktoc/blob/master/dist/mktoc-%s.tar.gz'
      % (VERSION,)),
   packages=['mktoc'],
   entry_points = {
      'console_scripts': ['mktoc = mktoc.cmdline:main',],
   },
   keywords = "cdrdao cue toc cd-writing audio-cd",
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

