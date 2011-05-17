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
   mktoc.base
   ~~~~~~~~~~

   Standard defines used by all modules.

   All modules in this package import this file into its root namespace.
"""

__date__       = '$Date$'
__version__    = '$Revision$'

__all__        = ['__author__', '__copyright__', '__email__', '__license__',
                  'VERSION', 'MkTocError' ,'FileNotFoundError', 'ParseError',
                  'UnderflowError', 'EmptyCueData' ]

#: Project author string.
__author__     = 'Patrick C. McGinty'
#: Project copyright string.
__copyright__  = 'Copyright (c) 2009'
#: Project e-mail address.
__email__      = 'mktoc[@]tuxcoder[dot]com'
#: Project license string.
__license__    = 'GPL'
#: Project version number string.
VERSION        = '1.1.3'

class MkTocError(Exception):
   """A base exception class for all mktoc exceptions classes."""
   pass

class FileNotFoundError(MkTocError):
   """Exception class used whenever a file can not be located and is
   required by the system."""
   pass

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

