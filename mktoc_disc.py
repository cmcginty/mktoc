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

__author__     = 'Patrick C. McGinty'
__email__      = 'mktoc[@]tuxcoder[dot]com'
__copyright__  = 'Copyright (c) 2008'
__license__    = 'GPL'
__date__       = '$Date$'

import os
import re
import wave

from mktoc_global import *
from mktoc_wav import WAV_REGEX
from mktoc_wav import WavFileCache

class Disc( object ):
   """"""
   def __init__(self):
      self.performer = None
      self.title     = None
      self.genre     = None
      self.date      = None
      self.discid    = None
      self.catalog   = None
      self._mode     = 'CD_DA'

   def __str__(self):
      """Write the TOC formatted disc information to file handle 'fh' arg. The
      'disc' dictionary contains all data for the disc."""
      out = ['%s' % self._mode]
      if self.catalog:   out += ['CATALOG "%s"' % self.catalog]
      out += ['CD_TEXT { LANGUAGE_MAP { 0:EN }\n\tLANGUAGE 0 {']
      if self.title:     out += ['\t\tTITLE "%s"' % self.title]
      if self.performer: out += ['\t\tPERFORMER "%s"' % self.performer]
      if self.discid:    out += ['\t\tDISC_ID "%s"' % self.discid]
      out += ['}}']
      return '\n'.join(out)

   def mung(self):
      """Modify the values in 'disc' dictionary arg, if needed."""
      pass

   def set_multisession(self):
      """Update Disc info for a multi-session CD"""
      self._mode = 'CD_ROM_XA'


##############################################################################
class Track( object ):
   """"""
   def __init__(self,num):
      """"""
      self.performer    = None
      self.title        = None
      self.isrc         = None
      self.dcp          = None
      self.four_ch      = None
      self.pre          = None
      self.pregap       = None

      self.num = num
      self.indexes = []   # a list of indexes in the track
      self.is_data = False

   def __str__(self):
      """"""
      if self.is_data: return ''    # do not print data tracks
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

      for idx in self.indexes:
         out.append( str(idx) )

      return '\n'.join(out)

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

   def __init__(self, num, time, file_, search_dir='.', file_exists=True):
      """"""
      self.num = int(num)
      self.time = TrackTime(time)
      self.cmd  = self.AUDIO
      self.file_ = file_
      try:  # attempt to find the WAV file for this index
         self.file_ = self._mung_file(file_, search_dir)
      except FileNotFoundError:
         # file not found, but 'file_exists' indicates that the file must exists
         if file_exists: raise
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
      return '\n'.join(out)

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
      fn = os.path.splitext(fn)[0]        # strip extension
      fn = os.sep + fn + '.wav'     # full file name to search
      # escape any special characters in the file, and the '$' prevents
      # matching if any extra chars come after the name
      fn_pat = re.escape(fn)  + '$'
      file_regex = re.compile( fn_pat, re.IGNORECASE)
      for f in WavFileCache(dir_):
         if file_regex.search(f):   # if match was found
            return f                # return match
      raise FileNotFoundError, file_


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
      if mn<0: raise UnderflowError, \
         'Track time calculation resulted in a negative value'
      return TrackTime((mn,sc,fr))

   def _to_str(self,m_s_f):
      """"""
      min_,sec,frm = m_s_f
      return '%02d:%02d:%02d'%(min_,sec,frm)

