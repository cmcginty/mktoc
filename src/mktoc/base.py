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
This module contains all global classes and defines for the mktoc application.
The current class objects are:

   MkTocError:
      A base exception class for all mktoc exceptions classes.

   FileNotFoundError:
      Exception class used whenever a file can not be located and is required by
      the system.

   ParseError:
      Exception class indicates that a CUE file could not be parsed do to
      unknown data.

   UnderflowError:
      Exception class used by the disc module to indicate that a track time
      subtraction has caused and underflow.

   EmptyCueData:
      Exception class indicates that the input CUE file or STDIN data was
      empty. The mktoc application interprets this as a normal condition and
      does not raise an error to the user other than returning a non-zero exit
      code.
"""

__date__       = '$Date$'
__version__    = '$Revision$'

__all__        = ['__author__', '__email__', '__copyright__', '__license__', \
                  'VERSION', 'MkTocError' ,'FileNotFoundError', 'ParseError', \
                  'UnderflowError', 'EmptyCueData' ]

__author__     = 'Patrick C. McGinty'
__email__      = 'mktoc[@]tuxcoder[dot]com'
__copyright__  = 'Copyright (c) 2008'
__license__    = 'GPL'

VERSION        = '1.1.2'

class MkTocError(Exception): pass
class FileNotFoundError(MkTocError): pass
class ParseError(MkTocError): pass
class UnderflowError(MkTocError): pass
class EmptyCueData(MkTocError): pass

