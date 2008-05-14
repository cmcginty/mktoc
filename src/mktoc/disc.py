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
Module for mktoc that defines data structures to hold information related to an
audio CD. The following object classes are:

   Disc
      Holds audio disc metadata values such as album title, performer, genre.

   Track
      Holds track metadata values such as title and performer. Each track
      object contains a list of TrackIndexes that specifies the audio data
      associated with the track.

   TrackIndex
      Holds audio data location and specific TrackTime objects that specify the
      indexs starting and ending time.
"""

__date__    = '$Date$'
__version__ = '$Revision$'

import os
import re
import wave
import logging

from mktoc.base import *

__all__ = [ 'Disc', 'Track', 'TrackIndex' ]

log = logging.getLogger('mktoc.disc')


class Disc( object ):
   """Stores audio disc metadata values such as album title, performer, genre.

   Public Data Members:
      catalog
         A string representing the Catalog Id of a disc.

      date
         A string representing the release year of a disc.

      discid
         A string representing the DiscID value of a disc. This value is
         assumed to be correct and not verified by any internal logic.

      genre
         A string representing the genre of a disc

      performer
         A string representing the performer or artist of a disc.

      title
         A string representing the album title of a disc.

   Private Data Members:
      _mode
         A string that defines the write mode of disc. The default value is
         CD_DA which defines a standard audio CD. It is also possible to be
         changed to define a multi-session audio CD.
   """
   def __init__(self):
      """Initialize all data members to default values."""
      self.catalog   = None
      self.date      = None
      self.discid    = None
      self.genre     = None
      self.performer = None
      self.title     = None
      self._mode     = 'CD_DA'

   def __str__(self):
      """Return a string of TOC formatted disc information."""
      out = ['%s' % self._mode]
      if self.catalog:   out += ['CATALOG "%s"' % self.catalog]
      out += ['CD_TEXT { LANGUAGE_MAP { 0:EN }\n\tLANGUAGE 0 {']
      if self.title:     out += ['\t\tTITLE "%s"' % self.title]
      if self.performer: out += ['\t\tPERFORMER "%s"' % self.performer]
      if self.discid:    out += ['\t\tDISC_ID "%s"' % self.discid]
      out += ['}}']
      return '\n'.join(out)

   def mung(self):
      """Converts the class data to a corrected and standardized format."""
      pass

   def setMultisession(self):
      """Updates the class to a multi-session CD mode by changing the output
      mode value."""
      self._mode = 'CD_ROM_XA'


##############################################################################
class Track( object ):
   """Holds track metadata values such as title and performer. Each track
   object contains a list of TrackIndexes that specifies the audio data
   associated with the track.

   Public Data Members:
      dcp
         True or False, indicates 'Digital Copy Protection' flag on the track.

      four_ch
         True or False, indicates 'Four Channel Audio' flag on the track.

      indexes
         A list of TrackIndex objects. Every track has at least one TrackIndex
         and possibly more. The TrackIndex defines a length of audio data or
         property in the track. The fist TrackIndex can be pre-gap data. Only
         one audio file can be associated with a TrackIndex, so if a track is
         composed of multiple audio files, there will be an >= number of
         TrackIndexes. See the TrackIndex class for more info.

      is_data
         True or False, indicates if a track is binary data and not audio. Data
         tracks will not produce any text when printed.

      isrc
         String representing ISRC value of the track.

      num
         Integer initialized to the value of the track number.

      performer
         String representing the track artist.

      pre
         True or False, indicates 'Pre-Emphasis' flag on the track.

      pregap
         A TrackTime value that indicates the pre-gap value of the current
         track. The pre-gap is a time length at the beginning of a track that
         will cause a CD player to count up from a negative time value before
         changing the track index number. The starting pre-gap value of a track
         is essentially the final audio at the end of the previous track.
         However, there is more than one way to designate the pregap in a
         track, therefore this variable is only used if the first TrackIndex
         in the track contains more than just the pre-gap audio.

      title
         A string representing the title of the track.
   """
   def __init__(self,num):
      """Create an empty list of TrackIndex objects, and assign track number.
      Initialize all other data members to default values.

      Parameters:
         num   : Integer of the track index in the audio CD"""
      self.dcp          = False
      self.four_ch      = False
      self.indexes      = []    # a list of indexes in the track
      self.is_data      = False
      self.isrc         = None
      self.num          = num
      self.performer    = None
      self.pre          = False
      self.pregap       = None
      self.title        = None

   def __str__(self):
      """Return the TOC formated representation of the Track object including
      the TrackIndex objects. Data tracks will not generate any output."""
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

   def appendIdx(self, idx):
      """Append a new TrackIndex object to the end of indexes list. It is
      assumed that TrackIndexes are added in correct order.

      Parameter:
         idx   : A new TrackIndex object that is being added to the Track
                 object."""
      self.indexes.append(idx)

   def mung(self,trk2):
      """For use after the Track is updated with all data and indexes, to fix
      any inconstancies or errors in the Track data.  This method must be
      called before the Track data is used. That is because before calling this
      method, the data can be in an inconsistent state.

      Parameters:
         trk2  : A Track object immediately following the current track. If
                 current track is the last one, then this value must be
                 'None'."""
      # current index and "next" index or None
      for idx,idx2 in map(None, self.indexes, self.indexes[1:]):
         #####
         # Set the LENGTH argument on a track that must stop before EOF
         #
         # details:  if TOC command for current track is AUDIOFILE, then if
         #           next track uses the same file, then current INDEX must
         #           end before the next track INDEX starts. Note:
         #           TrackIndex.INDEX cmds do not have 'len' values.
         if trk2 and idx.cmd == TrackIndex.AUDIO and \
               idx.file_ == trk2.indexes[0].file_:
            end_time = trk2.indexes[0].time
            idx.len_ = end_time - idx.time

         # modify index values
         idx.mung( idx2 )


##############################################################################
class TrackIndex(object):
   """
   Represent an 'index' of an audio CD track. Specifically, information about a
   location, length and type of audio data. Track objects can have one or more
   TrackIndexes to represent the audio data belonging to the track.

   Constants:
      PREAUDIO
         Indicates a TrackIndex that is pre-gap audio data only.

      AUDIO
         Indicates a TrackIndex of standard audio data or both pre-gap and
         audio.

      INDEX
         Indicates a TrackIndex after the start of a time stamp of a previous
         AUDIO TrackIndex object. There is no audio data associated with
         'INDEX' TrackIndexes.

      START
         Same as 'INDEX', but TrackIndex preceding it is was the pre-gap audio
         of the same Track.

   Public Data Members:
      cmd
         Integer set to PREAUDIO or AUDIO or INDEX or START. Indicate the mode
         of TrackIndex object. See above for more details.

      file_
         A string representing a WAV file's path and name. This is used to read
         the audio data of the TrackIndex.

      len_
         Empty string or TrackTime value that specifies the number of audio
         frames associated with the TrackIndex.  By default, this value will
         equal the total length of the WAV data, but might be truncated if the
         track starts after, or ends before the WAV data.

      num
         Integer specifying the location of the TrackIndex in the track. The
         first index 'num' is always 0.

      time
         TrackTime value that specifies the starting time index of the
         TrackIndex object relative to the start of the audio data. Usually
         this value is '0'.
   """
   PREAUDIO, AUDIO, INDEX, START = range(4)

   def __init__(self, num, time, file_):
      """Initializes the TrackIndex data using input args and default values.
      If possible the sample count of the TrackIndex is calculated by reading
      the WAV audio data.

      Parameters:
         num      : The index number position in the Track, starting at 0.

         time     : A TrackTime object that defines the indexes starting offset
                    in the audio data file.

         file_    : A string representing the path location of a WAV file
                    associated with this index."""
      self.cmd    = self.AUDIO
      self.file_  = file_
      self.num    = int(num)
      self.time   = TrackTime(time)
      # set length to maximum possible for now (total - start)
      file_len = self._file_len(self.file_)
      if file_len:
         self.len_ = file_len - self.time
      else: self.len_ = ''
      log.debug( 'creating index %s' % repr(self) )

   def __repr__(self):
      """Return a string used for debug logging."""
      return "'%s, %s'" % (self.file_, self.time)

   def __str__(self):
      """Return the TOC formated string representation of the TrackIndex
      object."""
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

   def mung(self, idx2):
      """For use after the TrackIndex is updated with all data, to fix any
      inconstancies or errors in the TrackIndex data. This method must be
      called before the TrackIndex data is used. That is because before calling
      this method, the data can be in an inconsistent state. In some cases a
      variable will be deleted because it is not required for the future
      functions of the object.

      Parameters:
         idx2  : TrackIndex object that immediately follows the current object
                 in a Track object. If this object is the last TrackIndex in
                 the Track object, then 'idx2' should be None."""
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

   def _file_len(self,file_):
      """Returns the number of audio samples in the WAV file, 'file_'. Called
      during __init__. If 'file_' can not be opened, None is returned.

      Parameters:
         file_    : a file name string relative to the cwd referencing a WAV
                    file."""
      if not os.path.exists(file_):
         return None
      w = wave.open(file_)
      frames = w.getnframes() / (w.getframerate()/75)
      w.close()
      return TrackTime(frames)


##############################################################################
class TrackTime(object):
   """Container class to represent the sample count or position in audio data.
   Allows mathematical operations to be easily performed on time positions.

   Constants:
      _FPS
         Defines the number of audio 'Frames Per Second'

      _SPM
         Defines the number of 'Seconds Per Minute'

      _FPM
         Defines the number of audio 'Frames Per Minute'

   Private Data Members:
      _time
         Tuple that stores the minutes, seconds, and frames values. The
         combination of these values can be used to calculate the total frame
         count."""
   _FPS = 75            # frames per second
   _SPM = 60            # second per minute
   _FPM = _FPS * _SPM   # frames per minute

   def __init__(self, arg=None):
      """Initializes the TrackTime object, normalizing the input data.

      Parameters:
         arg   : Variable representation of the value of the TrackTime object.
                 The allowed formats are:
                  a) String in the format 'MM:SS:FF'
                  b) Tuple in the format (M,S,F)
                  c) Integer of the total frame length
                  d) None, object is initialized to 0 length"""
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
      """Return string value of the TrackTime in format 'MM:SS:FF'."""
      return '%02d:%02d:%02d' % self._time

   def __ne__(self, other):
      """Return True if objects are NOT equal."""
      return self._time != other._time

   def __eq__(self, other):
      """Return True if objects are equal."""
      return self._time == other._time

   def __sub__(self, other):
      """Return result of 'self' - 'other'."""
      mn,sc,fr = map(lambda x,y: x-y, self._time, other._time)
      if fr<0: sc-=1; fr+=self._FPS
      if sc<0: mn-=1; sc+=self._SPM
      if mn<0: raise UnderflowError, \
         'Track time calculation resulted in a negative value'
      return TrackTime((mn,sc,fr))

