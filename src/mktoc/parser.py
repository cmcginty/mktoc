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

from mktoc.base import *
from mktoc.disc import *
from mktoc.wav  import *
from mktoc.progress_bar import *

__all__ = ['CueParser','WavParser']

log = logging.getLogger('mktoc.parser')


class Parser(object):
   """A generic CD TOC parsing class. This class provides a foundation of
   public and private methods to access and modify an audio CD track listing.

   Private Data Members:
      _disc
         Disc object that stores global disc info.

      _tracks
         Track object that stores track info.

      _file_map
         Dictionary to map input WAV files to actual files on the system. The
         map is for use in cases where the defined file name does not exactly
         match the file system WAV name.

      _files
         In-order list of WAV files that apply to the CD audio.

      _find_wav
         True or False, when True the WAV file must be found in the FS or an
         exception is raised.

      _wav_file_cache
         WavFileCache object that can quickly find WAV files in the local file
         system.

      _write_tmp
         True or False, when True any new WAV files will be created in /tmp.
   """

   def __init__(self, work_dir=os.curdir, find_wav=True, write_tmp=False):
      """Parses CUE file text data and initializes object data. The primary
      output of this function is to create the '_disc' and '_tracks' objects.
      All of the processed CUE data is stored in these two structures.

      Parameters:
         find_wav    : True/False, True causes exceptions to be raised if a WAV
                       file can not be found in the FS.

         work_dir    : Path location of the working directory.

         write_tmp   : True/False, True causes corrected WAV files to be
                       written to /tmp"""
      # init class options
      self._disc           = None
      self._tracks         = None
      self._file_map       = {}
      self._files          = []
      self._find_wav       = find_wav
      self._wav_file_cache = WavFileCache(work_dir)
      self._write_tmp      = write_tmp

   def getToc(self):
      """Access method to return a text stream of the CUE data in TOC
      format."""
      toc = []
      toc.extend( str(self._disc).split('\n') )
      for trk in self._tracks:
         toc.extend( str(trk).split('\n') )
      # expand tabs to 4 spaces, strip trailing white space on each line
      toc = [line.expandtabs(4).rstrip() for line in toc]
      return toc

   def modWavOffset(self,samples):
      """Optional method to correct the audio WAV data by shifting the samples
      by a positive or negative offset. This can be used to compensate for a
      write offset in a CD/DVD burner. If the '_write_tmp' variable is True,
      all new WAV files will be created in the /tmp directory.

      Parameters:
         samples  : the number of samples to shift the audio data by. This
                    value can be negative or positive."""
      # create WavOffset object, initialize sample offset and progress output
      wo = WavOffsetWriter( samples, ProgressBar('processing WAV files:') )
      new_files = wo.execute( self._files, self._write_tmp )

      # change all index file names to newly generated files
      file_map = dict( zip(self._files,new_files) )
      for trk in self._tracks:
         for idx in trk.indexes:
            log.debug( "updating index file '%s'", idx.file_ )
            idx.file_ = file_map[idx.file_]

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
            file_on_disk = self._wav_file_cache.lookup(file_)
         except FileNotFoundError:
            # file not found, but 'file_exists' indicates that the file
            # must exists
            if self._find_wav: raise
            else: file_on_disk = file_
         self._file_map[file_] = file_on_disk
         return file_on_disk


class CueParser(Parser):
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

      _wav_line_nums
         List of CUE file line numbers that correspond to the '_files' list of
         WAV file.

      _track_line_nums
         List used as a lookup table, indexed by track number, to map each CUE
         track to its line number in the CUE text.

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

   def __init__(self, fh, cue_dir=os.curdir, find_wav=True, write_tmp=False):
      """Parses CUE file text data and initializes object data. The primary
      output of this function is to create the '_disc' and '_tracks' objects.
      All of the processed CUE data is stored in these two structures.

      Parameters:
         fh          : An open file handle used to read the CUE text data

         cue_dir     : Path location of the CUE file's directory.

         find_wav    : True/False, True causes exceptions to be raised if a WAV
                       file can not be found in the FS.

         write_tmp   : True/False, True causes corrected WAV files to be
                       written to /tmp"""
      # init class options
      super(CueParser,self).__init__(cue_dir, find_wav, write_tmp)
      self._wav_line_nums     = []
      self._track_line_nums   = []

      self._part_search  = RegexStore( dict(self._FILE_REGEX + \
                                            self._TRACK_REGEX) )
      self._disc_search  = RegexStore( dict(self._FILE_REGEX + \
                                            self._DISC_REGEX) )
      self._tinfo_search = RegexStore( dict(self._FILE_REGEX + \
                                         self._TINFO_REGEX + self._TRACK_REGEX) )

      # create a list of regular expressions before starting the parse
      rem_regex   = re.compile( r'^\s*REM\s+COMMENT' )
      # parse disc into memory, ignore comments
      self._cue = [line.strip() for line in fh if not rem_regex.search(line)]
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

   def _active_file(self,trk_idx):
      """Returns the previous WAV file used before the start of 'trk_idx'."""
      tline = self._track_line_nums[trk_idx]
      for i,fline in enumerate(self._wav_line_nums):
         if fline > tline: break
         out_file = self._files[i]
      return out_file

   def _build_lookup_tbl(self):
      """Helper function to create the '_wav_line_nums' and '_track_line_nums'
      referenced in the full class documentation."""
      for i,txt in enumerate(self._cue):
         key,match = self._part_search.match(txt)
         if match is not None:
            if key == 'file':
               file_ = self._lookup_file_name( match.group(1) )
               self._files.append( file_ )
               self._wav_line_nums.append( i )
            elif key == 'track':
               self._track_line_nums.append( i )
            else: # catch unhandled patterns
               raise ParseError, "Unmatched key: '%s'" % key

   def _parse_all_tracks(self):
      """Return a list of Track objects that contain the track information
      from the fully parsed CUE text data."""
      return [self._parse_track(i) for i in range(len(self._track_line_nums))]

   def _parse_disc(self):
      """Return a Disc object that contains the disc information from the fully
      parsed CUE text data. This method implements the 'disc' scanning steps of
      the parser."""
      disc = Disc()
      # splice the cue list
      data = self._cue[:self._track_line_nums[0]]
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
      if num+1 < len(self._track_line_nums):
         data = self._cue[ self._track_line_nums[num]:\
                           self._track_line_nums[num+1] ]
      else:
         data = self._cue[ self._track_line_nums[num]: ]
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


##############################################################################
class WavParser(Parser):
   """A simple parser object that uses a list of WAV files to create a CD TOC.
   The class assumes that each WAV file is an individual track, in ascending
   order."""
   def __init__(self, wav_files, work_dir=os.curdir, find_wav=True,
                write_tmp=False):
      """Initialize the parser. The primary output of this function is to
      create the '_disc' and '_tracks' objects.

      Parameters:
         wav_files   : A list of WAV files to add to the TOC

         word_dir    : Path location of the CUE file's directory.

         find_wav    : True/False, True causes exceptions to be raised if a WAV
                       file can not be found in the FS.

         write_tmp   : True/False, True causes corrected WAV files to be
                       written to /tmp"""
      # init class options
      super(WavParser,self).__init__(work_dir, find_wav, write_tmp)
      self._files = [self._lookup_file_name(f) for f in wav_files]
      # create Disc and Track objects to represent data
      self._disc     = Disc()
      self._tracks   = []
      for i,file_ in enumerate(self._files):
         # create a new track for the WAV file
         trk = Track(i+1)
         # add the WAV file to the first index in the track
         trk.appendIdx( TrackIndex(1,0,file_) )
         # add the new track to the track list
         self._tracks.append( trk )
      # modify data to workable formats
      self._disc.mung()
      # current track and "next" track or None
      for trk,trk2 in map(None, self._tracks, self._tracks[1:]):
         trk.mung(trk2)   # update value in each track before printing


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

