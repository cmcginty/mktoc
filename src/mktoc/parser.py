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

import os
import re
from StringIO import StringIO

from mktoc.base import *
from mktoc.base import __author__, __email__, __copyright__, __license__
from mktoc.base import __version__
from mktoc.disc import Disc,Track,TrackIndex
from mktoc.wav import WavOffsetWriter
from mktoc.progress_bar import ProgressBar

__date__ = '$Date$'

class CueParser(object):
   """"""
   # global search pattern unused in all other searches
   _FILE_REGEX  = [
      ('file',  r"""
         ^\s*FILE       # FILE
         \s+"(.*)"      # 'file name' in quotes
         \s+WAVE$       # WAVE
      """ )]

   # create search patterns for lookup table parsing
   _TRACK_REGEX = [
      ('track',  r"""
         ^\s*TRACK                  # TRACK
         \s+(\d+)                   # track 'number'
         \s+(AUDIO|MODE.*)$         # AUDIO or MODEx/xxxx
      """)]

   # create search patterns for disc parsing
   _DISC_REGEX = [
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
   _TINFO_REGEX = [
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

   def __init__(self, fh, find_wav=True, cue_dir='.', write_tmp=False, **unk):
      """"""
      # init class options
      self._find_wav    = find_wav
      self._cue_dir     = cue_dir
      self._write_tmp   = write_tmp
      self._file_tbl    = []
      self._track_tbl   = []

      self._part_search  = RegExDict( dict(self._FILE_REGEX + self._TRACK_REGEX) )
      self._disc_search  = RegExDict( dict(self._FILE_REGEX + self._DISC_REGEX) )
      self._tinfo_search = RegExDict( dict(self._FILE_REGEX + self._TINFO_REGEX + \
                                             self._TRACK_REGEX) )

      # create a list of regular expressions before starting the parse
      rem_regex   = re.compile( r'^\s*REM\s+COMMENT' )
      # parse disc into memory, ignore comments
      self._cue = [l.strip() for l in fh.readlines() if not rem_regex.search(l)]
      if not len(self._cue):
         raise EmptyCueData
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
      buf = StringIO()
      print >> buf, str(self._disc)
      for trk in self._tracks:
         print >> buf, str(trk)
      return self._strip_buf(buf)

   def mod_wav_offset(self,samples):
      """"""
      files = [x[1] for x in self._file_tbl]
      # create WavOffset object, initialize sample offset and progress output
      wo = WavOffsetWriter( samples, ProgressBar('processing WAV files:') )
      new_files = wo.execute( files, self._write_tmp )

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
            raise ParseError, "Unmatched pattern in stream: '%s'" % txt
         # ignore 'file' matches
         if re_key == 'file': continue
         # assume all other matches are valid
         key,value = match.groups()
         key = key.lower()
         if hasattr(disc,key):
            # add match value to Disc object
            disc.__setattr__(key, value.strip())
         else:
            raise ParseError, "Unmatched keyword in stream: '%s'" % txt
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
            raise ParseError, "Unmatched pattern in stream: '%s'" % txt
         elif re_key == 'track':
            assert trk.num == int(match.group(1))
            if match.group(2) != 'AUDIO':
               trk.is_data = True
               self._disc.set_multisession()     # disc is multi-session
         elif re_key == 'file':
            # update file name
            file_name = match.group(1)
         elif re_key == 'index':
            # track INDEX, file_name is associated with the index
            idx_num,time = match.groups()
            i = TrackIndex(idx_num, time, file_name,
                           file_exists = self._find_wav,
                           search_dir  = self._cue_dir)
            trk.append_idx( i )
         elif re_key == 'quote' or re_key == 'named':
            # track information (PERFORMER, TITLE, ...)
            key,value = match.groups()
            key = key.lower()
            if hasattr(trk,key):    # add match value to Disc object
               trk.__setattr__(key, value.strip())
            else:
               raise ParseError, "Unmatched keyword in stream: '%s'" % txt
         elif re_key == 'flag':
            for f in [f.strip() for f in match.group(1).split()]:
               if re.search(r'DCP|4CH|PRE',f):     # flag must be known
                  if f == '4CH': f = 'four_ch'     # change '4CH' flag name
                  trk.__setattr__(f.lower(), True)
         else: # catch unhandled patterns
            raise ParseError, "Unmatched pattern in stream: '%s'" % txt
      return trk

   def _strip_buf(self,buf):
      """"""
      # cleanup string data
      buf.seek(0,os.SEEK_SET)
      data = [x.expandtabs(4).rstrip() for x in buf.readlines()]
      data = [x+'\n' for x in data]
      buf.close()
      # output to buffer, fix white-space
      buf = StringIO()
      buf.writelines( data )
      buf.seek(0,os.SEEK_SET)
      return buf


##############################################################################
class RegExDict(object):
   """"""
   def __init__(self, pat_dict):
      """"""
      # build RegEx searches
      re_searches   = [re.compile(pat, re.VERBOSE) for pat in pat_dict.values()]
      self._searches = dict(zip(pat_dict.keys(),re_searches))

   def match( self, text ):
      """"""
      for key,cre in self._searches.items():
         match = cre.search(text)
         if match: break    # break on first match
      return key,match

