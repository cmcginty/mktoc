#  Copyright (c) 2011, Patrick C. McGinty
#
#  This program is free software: you can redistribute it and/or modify it
#  under the terms of the Simplified BSD License.
#
#  See LICENSE text for more details.
"""
   mktoc.base
   ~~~~~~~~~~

   Standard defines used by all modules.

   All modules in this package import this file into its root namespace.
"""

__all__        = ['__author__', '__copyright__', '__email__', '__license__',
                  'VERSION', 'MkTocError' ,'FileNotFoundError',
                  'TooManyFilesMatchError', 'ParseError', 'UnderflowError',
                  'EmptyCueData' ]

#: Project author string.
__author__     = 'Patrick C. McGinty'
#: Project copyright string.
__copyright__  = 'Copyright (c) 2011'
#: Project e-mail address.
__email__      = 'mktoc[@]tuxcoder[dot]com'
#: Project license string.
__license__    = 'BSD'
#: Project version number string.
VERSION        = '1.1.3'

class MkTocError(Exception):
   """A base exception class for all mktoc exceptions classes."""
   pass

class FileNotFoundError(MkTocError):
   """Exception class used whenever a file can not be located and is
   required by the system."""
   pass

class TooManyFilesMatchError(MkTocError):
   """Exception class used whenever multiple files are found that match the
   source file required by the system."""
   def __init__(self,src_file,found_files):
      self.src_file = src_file
      self.found_files = found_files

class ParseError(MkTocError):
   """Exception class indicates that a CUE file could not be parsed do to
   unknown data."""
   pass

class UnderflowError(MkTocError):
   """Exception class used by the disc module to indicate that a track
   time subtraction has caused and underflow."""
   pass

class EmptyCueData(MkTocError):
   """Exception class indicates that the input CUE file or STDIN data was
   empty.  The mktoc application interprets this as a normal condition and
   does not raise an error to the user other than returning a non-zero
   exit code."""
   pass

