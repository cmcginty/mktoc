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
   This program simplifies the creation of audio CDs when burning with
   cdrdao. Specifically, it will convert an ExactAudioCopy (EAC) CUE
   file to the TOC format that is readable by cdrdao.

   This program focuses primarily on EAC CUE files. It includes support
   for non-compliant CUE files, including pregaps at the end of previous
   tracks.  There are additional features to detect and fix incorrect
   file path names and extension types.

Usage:
   mktoc [OPTIONS] [CUE_FILE]
   mktoc [OPTIONS] [CUE_FILE] -o [TOC_FILE]
   mktoc [OPTIONS] < CUE_FILE

   CUE_FILE must contain a valid CUE format. When FILE is not provided,
   the program will read from STDIN. All output will be sent to STDOUT.

   All attempts will be made to preserve any and all information from
   the input file. For any case where the CUE file contains unknown or
   bad values, the user will be notified on STDERR.

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
   """"""
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
      cue_parse.mod_wav_offset( opt.wav_offset )
   data = cue_parse.get_toc()
   fh_out.write( banner_msg() )
   fh_out.write( data.read() )
   data.close()

   fh_in.close()
   fh_out.close()

def banner_msg():
   """Write a TOC comment header to file handle 'fh'"""
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
   """ % (EMAIL,e)

def error_msg_file(e):
   """Print a default error message to the user."""
   print >> sys.stderr, """
   ERROR! -- Could not locate WAV file:
   --->  '%s'

   Cdrdao can not correctly write pregaps in TOC files without explicit file
   lengths. If you know what you are doing, you can disable this check with
   the '%s' option.
   """ % (e,_OPT_ALLOW_WAV_FNF)


##############################################################################
if __name__ == '__main__':
   global progName
   progName = os.path.basename(sys.argv[0])
   try:
      main()
   except FileNotFoundError, e:
      error_msg_file(e)
   except MkTocError, e:
      error_msg(e)
   except Exception:
      traceback.print_exc()
   except: pass      # ignore base exceptions (exit,key-int)
   else: exit(0)     # no exception, exit success
   exit(1)           # exit with failure

