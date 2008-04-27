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
Description:
   mktoc simplifies the steps needed to create audio CD TOC files for the
   cdrdao CD burning program. For users familiar with ExactAudioCopy or CdrWin,
   TOC files are synonymous with CUE sheets. The primary goal of mktoc is to
   create TOC files using a previously generated CUE sheet.

Features:

    * Convert an ExactAudioCopy (EAC) CUE file to the TOC format that is usable
      by cdrdao.
    * Non-compliant CUE sheet support.
    * Support for various pregap methods.
    * Can create offset corrected WAV files for true 'bit-for-bit' accurate
      copies.
    * Fuzzy file name logic can correct common file name spelling variations.
    * Workaround known TOC file parsing bugs in cdrdao.

Usage:
   mktoc [OPTIONS] [CUE_FILE]
   mktoc [OPTIONS] [CUE_FILE] -o [TOC_FILE]
   mktoc [OPTIONS] < CUE_FILE

   CUE_FILE must contain a valid CUE format. When FILE is not provided, the
   program will read from STDIN. All output will be sent to STDOUT.

   All attempts will be made to preserve any and all information from the input
   file. For any case where the CUE file contains unknown or bad values, the
   user will be notified on STDERR.

Options:
   --version
         show program's version number and exit

   -h, --help
         show help message and exit

   -a, --allow-missing-wav
         do not abort when WAV file(s) are missing, (experts only). It is
         possible when using this option that a bug in cdrdao will create a CD
         that ignores the pre gap definitions in the TOC file. Only use this
         option if the CUE file does not contain pre gaps, or if you do not
         wish to retain the pre gap information.

   -c WAV_OFFSET, --offset-correction=WAV_OFFSET
         correct reader/writer offset by creating WAV file(s) shifted by
         WAV_OFFSET samples (original data is not modified)

   -f CUE_FILE, --file=CUE_FILE
         specify the input CUE file to read

   -o TOC_FILE, --output=TOC_FILE
         specify the output TOC file to write

   -t, --use-temp
        write offset corrected WAV files to /tmp directory

Examples:

   1) Display the TOC file, given an input CUE file:

      mktoc cue_file.cue
      mktoc < cue_file.cue
      mktoc -f cue_file.cue

   2) Write a TOC file to 'toc_file.toc', given an input CUE file:

      mktoc cue_file.cue toc_file.toc
      mktoc < cue_file.cue > toc_file.toc
      mktoc -f cue_file.cue -o toc_file.toc

   3) Tell mktoc to ignore missing WAV file errors, possible causing incorrect
      TOC file results (see above).

      mktoc -a cue_file.cue

   4) Adjust WAV files for a CD writer offset value. For example, if your CD
      writer has a -30 sample write offset, it can be corrected by offsetting
      the input WAV files by +30 samples. New wav files will be placed in the
      working directory in a new dir called 'wav+30'

      mktoc -c 30 < cue_file.cue

   5) Adjust WAV files for a CD writer offset value, but create new files in
      the /tmp directory.

      mktoc -c 30 -t < cue_file.cue

E-mail:
   mktoc[@]tuxcoder[dot]com

Info:
   http://mktoc.googlecode.com
   http://blog.tuxcoder.com
"""

import os
import sys
import traceback
from optparse import OptionParser
from mktoc.base import *
from mktoc.base import __author__, __email__, __copyright__, __license__
from mktoc.base import __version__
from mktoc.parser import CueParser

__date__ = '$Date$'

# WAV file reading command-line switch
#  - allow 'file not found' errors when reading WAV files
_OPT_ALLOW_WAV_FNF   = '-a'
# Offset correction command-line switch
# - enable output of offset corrected WAV files
_OPT_OFFSET_CORRECT  = '-c'
# Temp WAV Files
# - write offset corrected WAV files to /tmp dir
_OPT_TEMP_WAV        = '-t'

def main():
   """Starting execution point. Interprets all program arguments and creates a
   CueParser object to generate a final TOC file."""
   usage = '[OPTIONS] CUE_FILE TOC_FILE'
   parser = OptionParser( usage='%prog '+usage,
                          version='%prog '+__version__ )

   parser.add_option( _OPT_ALLOW_WAV_FNF, '--allow-missing-wav',
         dest='find_wav', action="store_false", default=True,
         help='do not abort when WAV file(s) are missing, (experts only)')
   parser.add_option( _OPT_OFFSET_CORRECT, '--offset-correction',
         dest='wav_offset', type='int',
         help='correct reader/writer offset by creating WAV file(s) shifted by '\
         'WAV_OFFSET samples (original data is not modified)' )
   parser.add_option('-f', '--file', dest='cue_file',
         help='specify the input CUE file to read')
   parser.add_option('-o', '--output', dest='toc_file',
         help='specify the output TOC file to write')
   parser.add_option(_OPT_TEMP_WAV, '--use-temp', dest='write_tmp',
         action='store_true', default=False,
         help='write offset corrected WAV files to /tmp directory' )
   opt,args = parser.parse_args()

   # verify input arguments
   if len(args)>2 or \
         (len(args)>=1 and opt.cue_file) or \
         (len(args)>=2 and opt.toc_file):
      parser.error("Ambiguous file arguments!")
   if len(args)>=1: opt.cue_file = args[0]
   if len(args)>=2: opt.toc_file = args[1]
   # test "WAV file not found" and "offset correction" argument combination
   if opt.wav_offset and not opt.find_wav:
      parser.error("Can not combine '%s' and '%s' options!" % \
                     (_OPT_ALLOW_WAV_FNF,_OPT_OFFSET_CORRECT) )
   # test "offset correction" and "temp WAV" argument combination
   if opt.write_tmp and not opt.wav_offset:
      parser.error("Can not use '%s' wihtout '%s' option!" % \
                     (_OPT_TEMP_WAV, _OPT_OFFSET_CORRECT) )
   # open CUE file
   if opt.cue_file:
      # set the working dir of the input file
      opt.cue_dir = os.path.dirname( opt.cue_file )
      try:
         fh_in = open(opt.cue_file)
      except:
         print >> sys.stderr, sys.exc_value
         exit(-1)
   else:
      fh_in = sys.stdin
   # open TOC file
   if opt.toc_file:
      try:
         fh_out = open(opt.toc_file,'w')
      except:
         print >> sys.stderr, sys.exc_value
         exit(-1)
   else:
      fh_out = sys.stdout

   # !! Main program steps begin here !!
   cue_parse = CueParser(fh_in, **opt.__dict__)
   if opt.wav_offset:
      cue_parse.modWavOffset( opt.wav_offset )
   data = cue_parse.getToc()
   fh_out.write( banner_msg() )
   fh_out.write( data.read() )
   data.close()

   fh_in.close()
   fh_out.close()

def banner_msg():
   """Returns a TOC comment header that is placed at the top of the TOC file."""
   return "// Generated by %s %s\n" % (progName, __version__) + \
      "// %s, %s\n" % (__copyright__, __author__) + \
      "// Report bugs to <%s>\n" % __email__

def error_msg(e):
   """Print a default error message to the user."""
   print >> sys.stderr, """
   ERROR! -- An unrecoverable error has occurred. If you believe the CUE file
   is correct, please send the input file to <%s>,
   along with the error message below.

   ---> %s
   """ % (__email__,e)

def error_msg_file(e):
   """Print a missing WAV file error message to the user."""
   print >> sys.stderr, """
   ERROR! -- Could not locate WAV file:
   --->  '%s'

   Cdrdao can not correctly write pregaps in TOC files without explicit file
   lengths. If you know what you are doing, you can disable this check with
   the '%s' option.
   """ % (e,_OPT_ALLOW_WAV_FNF)


##############################################################################
if __name__ == '__main__':
   """Call the main() function and catch any exceptions."""
   global progName
   progName = os.path.basename(sys.argv[0])
   try:
      main()
   except EmptyCueData: pass     # ignore NULL data input (Ctrl-C)
   except FileNotFoundError, e:
      error_msg_file(e)
   except MkTocError, e:
      error_msg(e)
   except Exception:
      traceback.print_exc()
   except: pass      # ignore base exceptions (exit,key-int)
   else: exit(0)     # no exception, exit success
   exit(1)           # exit with failure

