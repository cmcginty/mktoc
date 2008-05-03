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
Module for mktoc that provides object(s) to parse text files describing the
layout of an audio CD. After the parse step is complete, it is possible to
access the data or convert into any other output format. The following object
classes are:

   CueParser
      An audio CUE sheet text file parsing class. After parsing, the CUE file
      can be re-created or converted into a new format.

   RegexStore
      A helper class that simplifies the management of regular expressions. The
      RegexStore class is used to apply a list of regular expressions to a
      single text stream. The first matching regular expression is returned.
"""

__date__    = '$Date$'
__version__ = '$Revision$'

import os
import re
import logging
from StringIO import StringIO

from mktoc.base import *
from mktoc.disc import *
from mktoc.wav  import *
from mktoc.progress_bar import *

__all__ = ['CueParser']

log = logging.getLogger('mktoc.parser')


class CueParser(object):
   """An audio CUE sheet text file parsing class. By matching the known format
   of a CUE file, the relevant text information is extracted and converted to a
   binary representation. The binary representation is created by using
   combination of Disc, Track, and TrackIndex objects. With the data, the CUE
   file can be re-created or converted into a new format.

   Constants:
      The following constants contain all of the pattern matching expressions
      for the CUE file parsing steps. The patterns are combined and applied
      depending on the current step of the scanning process.

      _FILE_REGEX
         Regex patterns for WAV file names.

      _TRACK_REGEX
         Regex patterns for Track commands.

      _DISC_REGEX
         Regex patterns for Disc info.

      _TINFO_REGEX
         Regex patterns for associated Track info.

   Private Data Members:
      _cue
         List of processed CUE text data. The processing step removes text
         comments and strips white spaces.

      _disc
         Disc object that store the parsed CUE disc info.

      _tracks
         Track object that stores the parsed CUE track info.

      _file_map
         Dictionary to map CUE file names to WAV files on the system. The map
         is for use in cases where the CUE defined file name does not exactly
         match the file system WAV name.

      _file_tbl
         In-order list of tuples containing a WAV files found in the CUE text,
         and the line number it was found on. The line number is the first
         element of the tuple.

      _find_wav
         True or False, when True the WAV file must be found in the FS or an
         exception is raised.

      _track_tbl
         List used as a lookup table, indexed by track number, to map each CUE
         track to its line number in the CUE text.

      _wav_files
         WavFileCache object that can quickly find WAV files in the local file
         system.

      _write_tmp
         True or False, when True any new WAV files will be created in /tmp.

      _part_search
         RegexStore list of regex searches for first partial scan of the TOC
         text.

      _disc_search
         RegexStore list of regex searches for disc info scan of the TOC

      _tinfo_search
         RegexStore list of regex searches for track info scan of the TOC
   """
   # file name search pattern used in all other searches
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

   def __init__(self, fh, find_wav=True, cue_dir=os.curdir,
                write_tmp=False, **unk):
      """Parses CUE file text data and initializes object data. The primary
      output of this function is to create the '_disc' and '_tracks' objects.
      All of the processed CUE data is stored in these two structures.

      Parameters:
         fh          : An open file handle used to read the CUE text data

         find_wav    : True/False, True causes exceptions to be raised if a WAV
                       file can not be found in the FS.

         cue_dir     : Path location of the CUE file's directory.

         write_tmp   : True/False, True causes corrected WAV files to be
                       written to /tmp

         unk         : accepts all unknown options to simplify invoke step"""
      # init class options
      self._file_map    = {}
      self._file_tbl    = []
      self._find_wav    = find_wav
      self._track_tbl   = []
      self._wav_files   = WavFileCache(cue_dir)
      self._write_tmp   = write_tmp

      self._part_search  = RegexStore( dict(self._FILE_REGEX + \
                                            self._TRACK_REGEX) )
      self._disc_search  = RegexStore( dict(self._FILE_REGEX + \
                                            self._DISC_REGEX) )
      self._tinfo_search = RegexStore( dict(self._FILE_REGEX + \
                                         self._TINFO_REGEX + self._TRACK_REGEX) )

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

   def getToc(self):
      """Access method to return a text stream of the CUE data in TOC
      format."""
      # create TOC file
      buf = StringIO()
      print >> buf, str(self._disc)
      for trk in self._tracks:
         print >> buf, str(trk)
      return self._strip_buf(buf)

   def modWavOffset(self,samples):
      """Optional method to correct the audio WAV data by shifting the samples
      by a positive or negative offset. This can be used to compensate for a
      write offset in a CD/DVD burner. If the '_write_tmp' variable is True,
      all new WAV files will be created in the /tmp directory.

      Parameters:
         samples  : the number of samples to shift the audio data by. This
                    value can be negative or positive."""
      files = list(zip(*self._file_tbl)[1]) # unzip file_tbl[1] to new list
      # create WavOffset object, initialize sample offset and progress output
      wo = WavOffsetWriter( samples, ProgressBar('processing WAV files:') )
      new_files = wo.execute( files, self._write_tmp )

      # change all index file names to newly generated files
      file_map = dict( zip(files,new_files) )
      for trk in self._tracks:
         for idx in trk.indexes:
            log.debug( "updating index file '%s'", idx.file_ )
            idx.file_ = file_map[idx.file_]

   def _active_file(self,trk_idx):
      """Returns the previous WAV file used before the start of 'trk_idx'."""
      tline = self._track_tbl[trk_idx]
      for fline,fn in self._file_tbl:
         if fline > tline: break
         out_file = fn
      return out_file

   def _build_lookup_tbl(self):
      """Helper function to create the '_file_tbl' and '_track_tbl' referenced
      in the full class documentation."""
      for i,txt in enumerate(self._cue):
         key,match = self._part_search.match(txt)
         if match is not None:
            if key == 'file':
               file_ = self._lookup_file_name( match.group(1) )
               self._file_tbl.append( (i,file_) )
            elif key == 'track':
               self._track_tbl.append( i )
            else: # catch unhandled patterns
               raise ParseError, "Unmatched key: '%s'" % key

   def _lookup_file_name(self,file_):
      """Attempts to return the path to a valid WAV file in the files system
      using the input 'file_' value. If the WAV file can not be found and
      '_find_wav' is True, then an exception is raised.

      Parameter:
         file  : audio file name parsed from the CUE text."""
      if self._file_map.has_key(file_):
         return self._file_map[file_]
      else:
         try:  # attempt to find the WAV file
            file_on_disk = self._wav_files.lookup(file_)
         except FileNotFoundError:
            # file not found, but 'file_exists' indicates that the file
            # must exists
            if self._find_wav: raise
            else: file_on_disk = file_
         self._file_map[file_] = file_on_disk
         return file_on_disk

   def _parse_all_tracks(self):
      """Return a list of Track objects that contain the track information
      from the fully parsed CUE text data."""
      return [self._parse_track(i) for i in range(len(self._track_tbl))]

   def _parse_disc(self):
      """Return a Disc object that contains the disc information from the fully
      parsed CUE text data. This method implements the 'disc' scanning steps of
      the parser."""
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
            setattr(disc, key, value.strip())
         else:
            raise ParseError, "Unmatched keyword in stream: '%s'" % txt
      return disc

   def _parse_track(self,num):
      """Return a Track object that contains a single track element from the
      parsed CUE text data. This method implements the 'track' scanning steps
      of the parser.

      Parameters:
         num   : the track index of the track to parse. The first track starts
                 at 0."""
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
               self._disc.setMultisession()     # disc is multi-session
         elif re_key == 'file':
            # update file name
            file_name = self._lookup_file_name(match.group(1))
         elif re_key == 'index':
            # track INDEX, file_name is associated with the index
            idx_num,time = match.groups()
            i = TrackIndex( idx_num, time, file_name )
            trk.appendIdx( i )
         elif re_key == 'quote' or re_key == 'named':
            # track information (PERFORMER, TITLE, ...)
            key,value = match.groups()
            key = key.lower()
            if hasattr(trk,key):    # add match value to Disc object
               setattr(trk, key, value.strip())
            else:
               raise ParseError, "Unmatched keyword in stream: '%s'" % txt
         elif re_key == 'flag':
            for f in [f.strip() for f in match.group(1).split()]:
               if re.search(r'DCP|4CH|PRE',f):     # flag must be known
                  if f == '4CH': f = 'four_ch'     # change '4CH' flag name
                  setattr(trk, f.lower(), True)
         else: # catch unhandled patterns
            raise ParseError, "Unmatched pattern in stream: '%s'" % txt
      return trk

   def _strip_buf(self, buf):
      """Helper function that re-formats a buffer of text data. The processing
      steps are:
            a) expand tabs to 4 spaces
            b) strip trailing white space on each line"""
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
class RegexStore(object):
   """A helper class that simplifies the management of regular expressions. The
   RegexStore class is used to apply a list of regular expressions to a single
   text stream. The first matching regular expression is returned.

   Private Data Members:
      _searches
         Dictionary of compiled regex's keyed by a user supplied string value.
   """
   def __init__(self, pat_dict):
      """Initialize the '_searches' dictionary using the 'pat_dict' parameter.

      Parameters:
         pat_dict : A dictionary of regular expression strings. The regex value
                    is compiled and stored in the '_searches' dictionary, keyed
                    by the original 'pat_dict' key."""
      # build RegEx searches
      re_searches = [re.compile(pat, re.VERBOSE) for pat in pat_dict.values()]
      self._searches = dict(zip(pat_dict.keys(),re_searches))

   def match( self, text ):
      """Applies the 'text' parameter to a dictionary of regex searches. The
      output of the first matching regex is returned along with the matching
      regex's dictionary key. The return is data is contained in a tuple, with
      the key as the first element.

      Parameters:
         text :   text string applied to a list of regex searches."""
      for key,cre in self._searches.items():
         match = cre.search(text)
         if match: break    # break on first match
      return key,match

