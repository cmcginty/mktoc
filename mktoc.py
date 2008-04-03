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

"""mktoc v1.0 // (c) 2008, Patrick C. McGinty, mktoc[@]tuxcoder[dot]com

Description:
   Convert an ExactAudioCopy (EAC) CUE file to the TOC format that is readable
   by 'cdrdao'.

   This program focuses primarily on EAC CUE files. It includes support for
   non-compliant CUE files, including pregaps at the end of previous tracks.
   There are additional features to detect and fix incorrect file path names and
   extension types.

Usage:
   mktoc [OPTIONS] [CUE_FILE]
   mktoc [OPTIONS] [CUE_FILE] -o [TOC_FILE]
   mktoc [OPTIONS] < CUE_FILE

   CUE_FILE must contain a valid CUE format. When FILE is not provided, the
   program will read from STDIN. All output will be sent to STDOUT.

   All attempts will be made to preserve any and all information from the input
   file. For any case where the CUE file contains unknown or bad values, the
   user will be notified on STDERR.

E-mail:
   mktoc[@]tuxcoder[dot]com

Info:
   http://blog.tuxcoder.com
"""

import os
import sys
import traceback
import re
import wave
import StringIO
import time
import tempfile
from optparse import OptionParser

NAME     = 'mktoc'
VER      = 'v1.0'
DATE     = '2008'
AUTHOR   = 'Patrick C. McGinty'
EMAIL    = 'mktoc[@]tuxcoder[dot]com'

WAV_REGEX = re.compile(r'\.wav$', re.IGNORECASE)

# WAV file reading command-line switch
#  - allow 'file not found' errors when reading WAV files
OPT_ALLOW_WAV_FNF    = '-a'
# Offset correction command-line switch
# - enable output of offset corrected WAV files
OPT_OFFSET_CORRECT   = '-c'
# Temp WAV Files
# - write offset corrected WAV files to /tmp dir
OPT_TEMP_WAV         = '-t'

class MkTocError(Exception): pass
class CueMathError(MkTocError): pass
class CueFileNotFoundError(MkTocError): pass
class CueParseError(MkTocError): pass
class CueUnderflowError(MkTocError): pass

def main():
   """"""
   usage = '[OPTIONS] CUE_FILE TOC_FILE'
   parser = OptionParser( usage='%prog '+usage,
                          version='%prog '+VER )

   parser.add_option( OPT_ALLOW_WAV_FNF, '--allow-missing-wav',
         dest='find_wav', action="store_false", default=True,
         help='do not abort when WAV file(s) are missing, (experts only)')
   parser.add_option( OPT_OFFSET_CORRECT, '--offset-correction',
         dest='wav_offset', type='int',
         help='correct reader/writer offset by creating WAV file(s) shifted by '\
         'WAV_OFFSET samples (original data is not modified)' )
   parser.add_option('-f', '--file', dest='cue_file',
         help='specify the input CUE file to read')
   parser.add_option('-o', '--output', dest='toc_file',
         help='specify the output TOC file to write')
   parser.add_option(OPT_TEMP_WAV, '--use-temp', dest='wav_temp',
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
                     (OPT_ALLOW_WAV_FNF,OPT_OFFSET_CORRECT) )
   # test "offset correction" and "temp WAV" argument combination
   if opt.wav_temp and not opt.wav_offset:
      parser.error("Can not use '%s' wihtout '%s' option!" % \
                     (OPT_TEMP_WAV, OPT_OFFSET_CORRECT) )
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
   fh_out.write( data.read() )
   data.close()

   fh_in.close()
   fh_out.close()

def banner_msg():
   """Write a TOC comment header to file handle 'fh'"""
   out =  ["// Generated by %s %s -- (c) %s, %s" % (NAME,VER,DATE,AUTHOR)]
   out += ["// Report bugs to <%s>" % EMAIL]
   return str.join('\n',out)

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
   """ % (e,OPT_ALLOW_WAV_FNF)


##############################################################################
class CueParser(object):
   """"""
   def __init__(self, fh, **opts):
      """"""
      # init class options
      self._opts = opts
      opts.setdefault('find_wav', True)
      opts.setdefault('cue_dir', '.')
      # global search pattern unused in all other searches
      file_regex  = [
         ('file',  r"""
            ^\s*FILE       # FILE
            \s+"(.*)"      # 'file name' in quotes
            \s+WAVE$       # WAVE
         """ )]

      # create search patterns for lookup table parsing
      track_regex = [
         ('track',  r"""
            ^\s*TRACK                  # TRACK
            \s+(\d+)                   # track 'number'
            \s+(AUDIO|MODE.*)$         # AUDIO or MODEx/xxxx
         """)]

      # create search patterns for disc parsing
      disc_regex = [
         ('rem' , r"""
            ^\s*REM           # match 'REM'
            \s+(\w+)          # match 'key'
            \s+(.*)$          # match 'value'
         """),
         ('quote', r"""
            ^\s*(\w+)         # match 'key'
            \s+"(.*)"$        # match 'value' surrounded with double quotes
         """),
         ('catalog', r"""
            ^\s*(CATALOG)     # CATALOG
            \s+(\d{13})$      # catalog 'value'
         """)]

      # create search patterns for track parsing
      tinfo_regex = [
         ('index', r"""
            ^\s*INDEX                  # INDEX
            \s+(\d+)                   # 'index number'
            \s+(\d{2}:\d{2}:\d{2})$    # 'index time'
         """),
         ('quote', r"""
            ^\s*(PERFORMER|TITLE)      # 'key'
            \s+"(.*)"$                 # 'value' surrounded with double quotes
         """),
         ('named', r"""
            ^\s*(ISRC|PREGAP)          # a known CUE command
            \s+(.*)$                   # single arg
         """),
         ('flag', r"""
            ^\s*FLAGS               # a FLAG command
            \s+(.*)$                # one or more flags
         """)]

      self._part_search  = RegExDict( dict(file_regex + track_regex) )
      self._disc_search  = RegExDict( dict(file_regex + disc_regex) )
      self._tinfo_search = RegExDict( dict(file_regex + tinfo_regex + \
                                             track_regex) )

      # create a list of regular expressions before starting the parse
      rem_regex   = re.compile( r'^\s*REM\s+COMMENT' )
      # parse disc into memory, ignore comments
      self._cue = [l.strip() for l in fh.readlines() if not rem_regex.search(l)]
      self._build_lookup_tbl()
      # create data objects for CUE info
      self._disc    = self._parse_disc()
      self._tracks  = self._parse_all_tracks()
      # modify data to workable formats
      self._disc.mung()
      # current track and "next" track or None
      for trk,trk2 in map(None, self._tracks, self._tracks[1:]):
         trk.mung(trk2)   # update value in each track before printing

   def get_toc(self):
      """"""
      # create TOC file
      buf = StringIO.StringIO()
      print >> buf, banner_msg()
      print >> buf, str(self._disc)
      for trk in self._tracks:
         print >> buf, str(trk)
      return self._strip_buf(buf)

   def mod_wav_offset(self,samples):
      """"""
      files = [y for x,y in self._file_tbl]
      # create WavOffset object, intialize sample offset and progress output
      wo = WavOffsetWriter( samples, self._show_progress )
      new_files = wo.execute( files, self._opt.wav_temp )
      sys.stderr.write('\n')        # add EOF to progress output

      # change all index file names to newly generated files
      file_map = dict( zip(files,new_files) )
      for trk in self._tracks:
         for idx in trk.indexes:
            idx.file_ = file_map[idx.file_]

   def _active_file(self,trk_idx):
      """"""
      tline = self._track_tbl[trk_idx]
      for fline,fn in self._file_tbl:
         if fline > tline: break
         out_file = fn
      return out_file

   def _build_lookup_tbl(self):
      """"""
      self._track_tbl = []
      self._file_tbl  = []
      for i,txt in enumerate(self._cue):
         key,match = self._part_search.match(txt)
         if match is not None:
            if key == 'file':
               self._file_tbl.append( (i,match.group(1)) )
            elif key == 'track':
               self._track_tbl.append( i )

   def _parse_all_tracks(self):
      """"""
      return [self._parse_track(i) for i in range(len(self._track_tbl))]

   def _parse_disc(self):
      """"""
      disc = Disc()
      # splice the cue list
      data = self._cue[:self._track_tbl[0]]
      for txt in data:
         re_key,match = self._disc_search.match( txt )
         if match is None:
            raise CueParseError, "Unmatched pattern in stream: '%s'" % txt
         # ignore 'file' matches
         if re_key == 'file': continue
         # assume all other matches are valid
         key,value = match.groups()
         try:
            # add match value to Disc object
            disc[ key.lower() ] = value.strip()
         except KeyError:
            raise CueParseError, "Unmatched keyword in stream: '%s'" % txt
      return disc

   def _parse_track(self,num):
      """"""
      # splice track data
      if num+1 < len(self._track_tbl):
         data = self._cue[ self._track_tbl[num]:self._track_tbl[num+1] ]
      else:
         data = self._cue[ self._track_tbl[num]: ]
      # lookup the previous file name
      file_name = self._active_file(num)

      # <-- This is the main track parsing step --->
      trk = Track(num+1)
      # Every CUE file has list of FILE, TRACK, and INDEX commands. The FILE
      # commands specify the active FILE for the following INDEX commands. The
      # TRACK indicate the logical beginning of a new TRACK info list with TITLE
      # and PERFORMER tags.
      for txt in data:
         re_key,match = self._tinfo_search.match( txt )
         if match is None:
            raise CueParseError, "Unmatched pattern in stream: '%s'" % txt
         elif re_key == 'track':
            assert trk.num == int(match.group(1))
            if match.group(2) != 'AUDIO': trk.is_data = True
         elif re_key == 'file':
            # update file name
            file_name = match.group(1)
         elif re_key == 'index':
            # track INDEX, file_name is associated with the index
            idx_num,time = match.groups()
            i = TrackIndex(idx_num, time, file_name,
                           file_exists = self._opts['find_wav'],
                           search_dir  = self._opts['cue_dir'])
            trk.append_idx( i )
         elif re_key == 'quote' or re_key == 'named':
            # track information (PERFORMER, TITLE, ...)
            key,value = match.groups()
            try:
               trk[ key.lower() ] = value.strip()
            except KeyError:
               raise CueParseError, "Unmatched keyword in stream: '%s'" % txt
         elif re_key == 'flag':
            for f in [f.strip() for f in match.group(1).split()]:
               if re.search(r'DCP|4CH|PRE',f):     # flag must be known
                  if f == '4CH':
                     trk.four_ch = True
                  else:
                     trk[f.lower()] = True
         else: # catch unhandled patterns
            raise CueParseError, "Unmatched pattern in stream: '%s'" % txt
      return trk

   def _show_progress( self, samp, total ):
      """"""
      if not hasattr(self,'_samp_count'):
         self._samp_count = 0
         self._start_time = time.time()
      self._samp_count += samp
      percent = float(self._samp_count) / total * 100
      time_dif = time.time() - self._start_time    # compute time from start
      if not time_dif == 0:
         samp_rate = self._samp_count / time_dif      # calculate sample/sec
         remain_time = (total-self._samp_count) / samp_rate # estimate time left
         remain_str = '\tETA [%d:%02d]' % divmod(remain_time,60)
      else:
         remain_str = '\tETA [?:??]'
      sys.stderr.write( '\rprocessing WAV files: %3d%% %s' % \
                           (percent, remain_str) )

   def _strip_buf(self,buf):
      """"""
      # cleanup string data
      buf.seek(0,os.SEEK_SET)
      data = [x.expandtabs(4).rstrip() for x in buf.readlines()]
      data = [x+'\n' for x in data]
      buf.close()
      # output to buffer, fix white-space
      buf = StringIO.StringIO()
      buf.writelines( data )
      buf.seek(0,os.SEEK_SET)
      return buf


##############################################################################
class FixedDict(object):
   """"""
   def __init__(self,keys):
      """"""
      # for each string in 'fields', add to object with 'None' value
      self.__dict__.update( map(None,keys,[None]) )

   def __setitem__(self,key,val):
      """"""
      if not self.__dict__.has_key(key):
         raise KeyError
      self.__dict__[key] = val


##############################################################################
class Disc( FixedDict ):
   """"""
   _keys = ['performer','title','genre','date','discid','catalog']

   def __init__(self):
      """"""
      super(Disc,self).__init__(self._keys)

   def __str__(self):
      """Write the TOC formatted disc information to file handle 'fh' arg. The
      'disc' dictionary contains all data for the disc."""
      out = ['CD_DA']
      if self.catalog:   out += ['CATALOG "%s"' % self.catalog]
      out += ['CD_TEXT { LANGUAGE_MAP { 0:EN }\n\tLANGUAGE 0 {']
      if self.title:     out += ['\t\tTITLE "%s"' % self.title]
      if self.performer: out += ['\t\tPERFORMER "%s"' % self.performer]
      out += ['}}']
      return str.join('\n',out)

   def mung(self):
      """Modify the values in 'disc' dictionary arg, if needed."""
      pass


##############################################################################
class RegExDict(object):
   """"""
   def __init__(self, pat_dict):
      """"""
      # split keys from regex
      re_keys = [ n for n in pat_dict.keys() ]
      # build RegEx searches
      re_searches   = [re.compile(pat, re.VERBOSE) for pat in pat_dict.values()]
      self._searches = dict(zip(re_keys,re_searches))

   def match( self, text ):
      """"""
      for key,cre in self._searches.items():
         match = cre.search(text)
         if match: break    # break on first match
      return key,match


##############################################################################
class Track( FixedDict ):
   """"""
   _keys = ['performer','title','isrc','dcp','four_ch','pre','pregap']

   def __init__(self,num):
      """"""
      super(Track,self).__init__(self._keys)
      self.num = num
      self.indexes = []   # a list of indexes in the track
      self.is_data = False

   def __str__(self):
      """"""
      if self.is_data == True: return ''    # do not print data tracks
      out = ['\n//Track %d' % self.num]
      out += ['TRACK AUDIO']
      if self.isrc:       out += ['\tISRC "%s"' % self.isrc]
      if self.dcp:        out += ['\tCOPY']
      if self.four_ch:    out += ['\tFOUR_CHANNEL_AUDIO']
      if self.pre:        out += ['\tPRE_EMPHASIS']
      out += ['\tCD_TEXT { LANGUAGE 0 {']
      if self.title:      out += ['\t\tTITLE "%s"' % self.title]
      if self.performer:  out += ['\t\tPERFORMER "%s"' % self.performer]
      out += ['\t}}']
      if self.pregap:     out += ['\tPREGAP %s' % self.pregap]

      for num,idx in enumerate(self.indexes):
         out.append( str(idx) )

      return str.join('\n',out)

   def append_idx(self,idx):
      """"""
      self.indexes.append(idx)

   def mung(self,trk2):
      """"""
      # current index and "next" index or None
      for idx,idx2 in map(None, self.indexes, self.indexes[1:]):
         #####
         # Set the LENGTH argument on a track that must stop before EOF
         #
         # details:  if TOC command for current track is AUDIOFILE, then if
         #           next track uses the same file, then current INDEX must
         #           end before the next track INDEX starts
         if trk2 and idx.cmd == TrackIndex.AUDIO and \
               idx.file_ == trk2.indexes[0].file_:
            end_time = trk2.indexes[0].time
            idx.len_ = end_time - idx.time

         # modify index values
         idx.mung( idx2 )


##############################################################################
class TrackIndex(object):
   """"""
   PREAUDIO, AUDIO, INDEX, START = range(4)

   def __init__(self, num, time, file_, **opts):
      """"""
      opts.setdefault('search_dir','.')
      opts.setdefault('file_exists',True)
      self.num = int(num)
      self.time = TrackTime(time)
      self.cmd  = self.AUDIO
      self.file_ = file_
      try:  # attempt to find the WAV file for this index
         self.file_ = self._mung_file(file_, opts['search_dir'])
      except CueFileNotFoundError:
         # notify the user that there was a failure
         if opts['file_exists']: raise
      # set length to maximum possible for now (total - start)
      file_len = self._file_len()
      if file_len:
         self.len_ = file_len - self.time
      else: self.len_ = ''

   def __str__(self):
      """"""
      out = []
      if self.cmd == self.AUDIO or \
         self.cmd == self.PREAUDIO:
         out += ['\tAUDIOFILE "%(file_)s" %(time)s %(len_)s' % self.__dict__]
      elif self.cmd == self.INDEX:
         out += ['\tINDEX %(time)s' % self.__dict__]
      elif self.cmd == self.START:
         out += ['\tSTART %(len_)s' % self.__dict__]
      else: raise Exception
      # add start command for pregap audio
      if self.cmd == self.PREAUDIO:
         out += ['\tSTART']
      return str.join('\n',out)

   def mung(self,idx2):
      """"""
      #####
      # Add 'START' command after pregap audio file
      #
      # details:  if 'index' is a track pregap (num == 0) and the file for
      #           'next index' is not the same, then designate the 'index' as
      #           a pregap audio only. The result is to place a TOC 'START'
      #           command between this 'index' and the 'next index' in the
      #           TOC file.
      #
      if self.num == 0 and idx2 and self.file_ != idx2.file_:
         self.cmd = self.PREAUDIO

      #####
      # There are two case below to handle when a single WAV file is used for
      # multiple internal track indexes. Usually these indexes are ignore by CD
      # players, but they should be part of the CD.
      if idx2 and self.file_ == idx2.file_:
         #####
         # Designate the 'true' start index of a track when the track data file
         # contains pregap data. This is done with the TOC command 'START'
         #
         # details:  if the current index is the pregap data (0), then the
         #           pregap must be set by changing the 'next' index cmd to
         #           'START', and the length of the pregap must be set.
         if self.num == 0:
            idx2.cmd = self.START
            idx2.len_ = idx2.time - self.time
            del idx2.time # remove for safety, do not use
         #####
         # Else not a pregap, change the TOC command for a new track to
         # 'INDEX' when a single logical 'track' has multiple index values
         # (by default, the TOC command is AUDIOFILE when a track has a
         # single index).
         #
         # details:  the outside 'if' guarantee that the current and next index
         #           use the same file. Also, since it is not a pregap the TOC
         #           format must use 'INDEX' keyword instead of AUDIOFILE. No
         #           other calculations are needed because INDEX is specified
         #           by file offset.
         else:
            idx2.cmd = self.INDEX
            del idx2.len_ # remove for safety, do not use

   def _file_len(self):
      """"""
      if not os.path.exists(self.file_):
         return None
      w = wave.open( self.file_ )
      frames = w.getnframes() / (w.getframerate()/75)
      w.close()
      return TrackTime(frames)

   def _mung_file(self, file_, dir_):
      """Mung the file name, to an existing WAV file name"""
      tmp_name = file_
      # convert a DOS file path to Linux
      tmp_name = tmp_name.replace('\\','/')
      # base case: file exists, and is has a 'WAV' extension
      if WAV_REGEX.search(tmp_name) and os.path.exists(tmp_name):
         return file_       # return match
      # case 2: file is locatable in path with a little work
      fn = os.path.basename(tmp_name)     # strip leading path
      fn,ext = os.path.splitext(fn)       # strip extension
      fn = os.sep + fn + '.wav'     # full file name to search
      # escape any special characters in the file, and the '$' prevents
      # matching if any extra chars come after the name
      fn_pat = re.escape(fn)  + '$'
      file_regex = re.compile( fn_pat, re.IGNORECASE)
      for f in WavFileCache(dir_):
         if file_regex.search(f):   # if match was found
            return f                # return match
      raise CueFileNotFoundError, file_


##############################################################################
class TrackTime(object):
   """Container class for CD track time values. Allows mathematical
   operations to be easily performed on time positions."""

   _FPS = 75            # frames per second
   _SPM = 60            # second per minute
   _FPM = _FPS * _SPM   # frames per minute

   def __init__(self,arg=None):
      """"""
      if type(arg) is str:
         # extract time from string
         val = [int(x) for x in arg.split(':')]
         self._time = tuple(val)
      elif type(arg) is tuple:
         # assume arg is correct format
         self._time = arg
      elif type(arg) is int:
         # convert frame count to min,sec,frames
         min_,fr = divmod(arg, self._FPM)
         sec,fr = divmod(fr, self._FPS)
         self._time = (min_,sec,fr)
      else:
         # set time to '0:0:0' (zero)
         self._time = tuple([0]*3)

   def __str__(self):
      """Return string value of object."""
      return self._to_str(self._time)

   def __repr__(self):
      """Return string value of object."""
      return self._to_str(self._time)

   def __ne__(self,other):
      """Return true if objects are equal."""
      return self._time != other._time

   def __eq__(self,other):
      """Return true if objects are equal."""
      return self._time == other._time

   def __sub__(self,other):
      """Return result of 'self' - 'other'."""
      mn,sc,fr = map(lambda x,y: x-y, self._time, other._time)
      if fr<0: sc-=1; fr+=self._FPS
      if sc<0: mn-=1; sc+=self._SPM
      if mn<0: raise CueUnderflowError, \
         'Track time calculation resulted in a negative value'
      return TrackTime((mn,sc,fr))

   def _to_str(self,m_s_f):
      """"""
      min_,sec,frm = m_s_f
      return '%02d:%02d:%02d'%(min_,sec,frm)


##############################################################################
class WavFileCache(list):
   """"""
   def __new__(cls, *args, **kwargs):
      inst = cls.__dict__.get('__instance__')
      if inst is None:
         cls.__instance__ = inst = list.__new__(cls)
         WavFileCache._init_cache(inst,*args,**kwargs)
      return inst

   # this line is required, or no elements will show up in the list
   def __init__(self,_dir): pass

   def _init_cache(self,_dir):
      """Return a list of files in the vicinity of the current working dir."""
      fc = 0
      for root, dirs, files in os.walk(_dir):
         if fc > 1000: break     # only cache first n files
         fc += len(files)
         f_tup = zip( [root]*len(files), files )
         wav_files = [os.path.join(r,f) for r,f in f_tup if WAV_REGEX.search(f)]
         self.extend( wav_files )


##############################################################################
class WavOffsetWriter(object):
   """"""
   _COPY_SIZE = 256*1024

   def __init__(self,offset_samples,data_cb):
      """"""
      self.offset = offset_samples
      self.data_cb = data_cb

   def execute(self, files, use_tmp_dir):
      """"""
      self._total_samp = self._get_total_samp( files )
      # positive offset correction, insert silence in first track,
      # all other tracks insert end data of previous track
      if self.offset > 0:
         # create a list of 'previous' file names
         f2_list = [None] + files[:-1]
         offsetter_fnct = self._insert_prv_end

      # negative offset correction, append silence to end of last track,
      # all other tracks append start data of next track
      elif self.offset < 0:
         # create a list of 'next' file names
         f2_list = files[1:] + [None]
         offsetter_fnct = self._append_nxt_start

      out_files = []
      for f in files:
         if not use_tmp_dir:
            out_files.append( self._get_new_name(f) )
         else:
            out_files.append( self._get_tmp_name(f) )

      for out_f, f, f2 in zip(out_files, files, f2_list):
         offsetter_fnct( out_f, f, f2 )
      # return a list of the new files names
      return out_files

   def _append_nxt_start(self, out_fn, fn, nxt_fn):
      """Negative offset correction"""
      wav_out = wave.open(out_fn, 'w')
      wav_in = wave.open(fn)
      # setup the output parameters
      bytes_p_samp = wav_in.getsampwidth() * wav_in.getnchannels()
      offset_bytes = abs(self.offset) * bytes_p_samp
      wav_out.setparams( wav_in.getparams() )
      # seek ahead sample offset amount
      wav_in.setpos( abs(self.offset) )
      # copy all frame date from 1st file into new file
      while True:
         data = wav_in.readframes(self._COPY_SIZE)
         if len(data) == 0: break
         wav_out.writeframes( data )
         self.data_cb( len(data)/bytes_p_samp, self._total_samp )
         del data
      wav_in.close()
      # finally copy the remaining data from the next track, or silence
      if nxt_fn:
         # copy offset frame date from next file into new file
         wav_in = wave.open(nxt_fn)
         data = wav_in.readframes( abs(self.offset) )
         assert len(data) == offset_bytes
         wav_out.writeframes( data )
         self.data_cb( len(data)/bytes_p_samp, self._total_samp )
      else:
         # write silence to end of last track
         data = '\x00' * offset_bytes
         wav_out.writeframes( data )
         self.data_cb( len(data)/bytes_p_samp, self._total_samp )
      del data
      wav_in.close()
      wav_out.close()

   def _get_new_name(self, f):
      """"""
      dir_,name = os.path.split(f)
      new_dir = os.path.join(dir_, 'wav%+d' % self.offset)
      if not os.path.exists(new_dir):
         os.mkdir( new_dir )
      return os.path.join( new_dir, name)

   def _get_total_samp(self, files):
      """"""
      count = 0
      for f in files:
         count += wave.open(f).getnframes()
      return count

   def _get_tmp_name(self, f):
      """"""
      if not hasattr(self, '_tmp_dir'):
         self._tmp_dir = tempfile.mkdtemp( prefix=NAME )
      return os.path.join( self._tmp_dir, os.path.basename(f) )

   def _insert_prv_end(self, out_fn, fn, prv_fn):
      """Positive offset correction"""
      wav_out = wave.open(out_fn, 'w')
      wav_in = wave.open(fn)
      # setup the output parameters
      bytes_p_samp = wav_in.getsampwidth() * wav_in.getnchannels()
      offset_bytes = self.offset * bytes_p_samp
      wav_out.setparams( wav_in.getparams() )
      wav_in.close()
      # if previous file exists, insert end of stream to new file
      if prv_fn:
         wav_in = wave.open(prv_fn)
         pos = wav_in.getnframes() - self.offset   # seek position
         wav_in.setpos( pos ) # seek to EOF - offset
         data = wav_in.readframes( self.offset )
         assert len(data) == offset_bytes
         wav_out.writeframes( data )
         self.data_cb( len(data)/bytes_p_samp, self._total_samp )
         wav_in.close()
      else:    # insert silence if no previous file
         data = '\x00' * offset_bytes
         wav_out.writeframes( data )
         self.data_cb( len(data)/bytes_p_samp, self._total_samp )
      # add original file data to output stream
      wav_in = wave.open( fn )
      samples = wav_in.getnframes() - self.offset
      while samples:
         data = wav_in.readframes( min(samples,self._COPY_SIZE) )
         samples -= len(data) / bytes_p_samp
         wav_out.writeframes( data )
         self.data_cb( len(data)/bytes_p_samp, self._total_samp )
         del data
      wav_in.close()
      wav_out.close()


##############################################################################
if __name__ == '__main__':
   err = -1
   try:
      main(); err = 0
   except SystemExit: pass
   except KeyboardInterrupt: pass
   except CueFileNotFoundError, e:
      error_msg_file(e)
   except MkTocError, e:
      error_msg(e)
   except:
      traceback.print_exc()
   exit(err)

