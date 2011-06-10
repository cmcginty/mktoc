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
   mktoc.disc
   ~~~~~~~~~~

   A set of classes for representation of audio CD information.

   The following are a list of the classes provided in this module:

   * :class:`Disc`
   * :class:`Track`
   * :class:`TrackIndex`
"""

__date__    = '$Date$'
__version__ = '$Revision$'

import os
import re
import wave
import logging
import itertools as itr

from mktoc.base import *

__all__ = [ 'Disc', 'Track', 'TrackIndex' ]

log = logging.getLogger('mktoc.disc')


class Disc( object ):
   """
   Stores audio disc metadata values such as album title, performer, genre.
   """
   #: disc mode string for single session
   MODE_SINGLE_SESSION  = 'CD_DA'
   #: disc mode string for multi sessions
   MODE_MULTI_SESSION   = 'CD_ROM_XA'
   #: String representing the Catalog Id of a disc.
   catalog   = None
   #: String representing the release year of a disc.
   date      = None
   #: String representing the DiscID value of a disc. This value is assumed to
   #: be correct and not verified by any internal logic.
   discid    = None
   #: String representing the genre of a disc
   genre     = None
   #: String representing the performer or artist of a disc.
   performer = None
   #: String representing the album title of a disc.
   title     = None

   def __init__(self):
      self.is_multisession = False

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

   def set_field(self, name, value):
      """
      Set a disc field value as a class attributes.

      This method provides additional formating to any data fields. For
      example, removing quoting and checking the field name.

      :param name: Field name to set
      :type  name: str

      :param value: Value of field
      :type  value: str

      :return: :data:`True` if field is written to the class data, or
               :data:`False`
      """
      name = name.lower()
      if hasattr(self,name):
         setattr(self,name,value.strip('"'))
         return True
      return False

   @property
   def is_multisession(self):
      """
      :return: :data:`True` if disc is defined as multi-sesssion.
      """
      return self._mode == self.MODE_MULTI_SESSION

   @is_multisession.setter
   def is_multisession(self,val):
      """
      Change the mode of a disc to either 'single-session' or 'multi-session'.

      :param val: :data:`True` if disc is multi-session, :data:`False`
                  otherwise.
      :type  val: bool
      """
      if val:  self._mode = self.MODE_MULTI_SESSION
      else:    self._mode = self.MODE_SINGLE_SESSION


class Track( object ):
   """
   Holds track metadata values such as title and performer. Each :class:`Track`
   object contains a list of :class:`TrackIndex`\s that specifies the
   audio data associated with the track.
   """

   #: :data:`True` or :data:`False`, indicates *Digital Copy Protection*
   #: flag on  the track.
   dcp          = False
   #: :data:`True` or :data:`False`, indicates *Four Channel Audio* flag
   #: on the track.
   four_ch      = False
   #: list of :class:`TrackIndex` objects. Every track has at
   #: least one :class:`TrackIndex` and possibly more. The
   #: :class:`TrackIndex` defines a length of audio data or property in
   #: the track. The fist :class:`TrackIndex` can be pre-gap data. Only
   #: one audio file can be associated with a :class:`TrackIndex`, so if a
   #: track is composed of multiple audio files, there will be an >=
   #: number of :class:`TrackIndex`\s.
   indexes      = None
   #: :data:`True` or :data:`False`, indicates if a track is binary data
   #: and not audio. Data tracks will not produce any text when printed.
   is_data      = False
   #: String representing ISRC value of the track.
   isrc         = None
   #: Integer initialized to the value of the track number.
   num          = None
   #: String representing the track artist.
   performer    = None
   #: :data:`True` or :data:`False`, indicates *Pre-Emphasis* flag on the
   #: track.
   pre          = False
   #: :class:`_TrackTime` value that indicates the pre-gap value of the
   #: current track. The pre-gap is a time length at the beginning of a
   #: track that will cause a CD player to count up from a negative time
   #: value before changing the track index number.  The starting pre-gap
   #: value of a track is essentially the final audio at the end of the
   #: previous track.  However, there is more than one way to designate
   #: the pregap in a track, therefore this variable is only used if the
   #: first :class:`TrackIndex` in the track contains more than just the
   #: pre-gap audio.
   pregap       = None
   #: String representing the title of the track.
   title        = None

   def __init__(self,num,is_data=False):
      """
      :param num: Track index in the audio CD.
      :type num:  int

      :param is_data: :data:`True` if track is data instead of audio.
      :type  is_data: bool
      """
      # create an empty list of :class:`TrackIndex` objects, and
      # assign track number.
      self.indexes   = []    # list of indexes in the track
      self.num       = num
      self.is_data   = is_data

   def __str__(self):
      """Return the TOC formated representation of the :class:`Track`
      object including the :class:`TrackIndex` objects. Data tracks will
      not generate any output."""
      if self.is_data:
         return ''     # do not output to TOC
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

   def set_field(self, name, value):
      """
      Set a track field value as a class attributes.

      This method provides additional formating to any data fields. For
      example, removing quoting and checking the field name.

      :param name: Field name to set
      :type  name: str

      :param value: Value of field
      :type  value: str

      :return: :data:`True` if field is written to the class data, or
               :data:`False`
      """
      name = name.lower()
      if hasattr(self,name):
         if isinstance(value,basestring):
            setattr(self,name,value.strip('"'))
         elif isinstance(value,bool):
            setattr(self,name,value)
         return True
      return False


class TrackIndex(object):
   """
   Represent an *index* of an audio CD track.

   Specifically, information about a location, length and type of audio data.
   :class:`Track` objects can have one or more :class:`TrackIndex`\s to
   represent the audio data belonging to the track.

   .. rubric:: Constants

   .. data:: PREAUDIO

      Indicates a :class:`TrackIndex` that is pre-gap audio data only.

   .. data:: AUDIO

      Indicates a :class:`TrackIndex` of standard audio data or both pre-gap
      and audio.

   .. data:: INDEX

      Indicates a :class:`TrackIndex` after the start of a time stamp of a
      previous :const:`AUDIO` :class:`TrackIndex` object. There is no audio
      data associated with *INDEX* :class:`TrackIndex`\s.

   .. data:: START

      Same as :const:`INDEX`, but :class:`TrackIndex` preceding it is was
      the pre-gap audio of the same :class:`Track`.

   .. rubric::  Attributes

   .. attribute:: file_

      String representing a WAV file's path and name. This is used to read the
      audio data of the :class:`TrackIndex`.

   .. attribute:: len_

      Empty string or :class:`_TrackTime` value that specifies the number of
      audio frames associated with the :class:`TrackIndex`. By default, this
      value will equal the total length of the WAV data, but might be truncated
      if the track starts after, or ends before the WAV data.

   .. attribute:: num

      Integer specifying the location of the :class:`TrackIndex` in the track.
      The first index *num* is always 0.

   .. attribute:: time

      :class:`_TrackTime` value that specifies the starting time index of the
      :class:`TrackIndex` object relative to the start of the audio data.
      Usually this value is ``0``.
   """

   #: Enum of valid :class:`TrackIndex` types.
   PREAUDIO, AUDIO, INDEX, START, DATA = range(5)

   #: Integer set to :const:`PREAUDIO` or :const:`AUDIO` or :const:`INDEX` or
   #: :const:`START`. Indicate the mode of :class:`TrackIndex` object.
   cmd = AUDIO

   def __init__(self, num, time, file_, len_=None):
      """
      If possible the sample count of the :class:`TrackIndex` is calculated by
      reading the WAV audio data.

      :param num:    Index number position in the :class:`Track`, starting
                     at 0.
      :type num:     int

      :param time:   The indexes starting offset in the audio data file.
      :type  time:   :class:`_TrackTime`

      :param file_:  String representing the path location of a WAV file
                     associated with this index.
      :type  file_:  str

      :param len_:   Track length in format supported by :class:`_TrackTime`.
      :type  len_:   str, tuple, int (see :class:`_TrackTime`)
      """
      self.file_  = file_
      self.num    = int(num)
      self.time   = _TrackTime(time)
      if len_:
         self.len_ = _TrackTime(len_)
      else:
         # set length to maximum possible for now (total - start)
         file_len = self._file_len(self.file_)
         if file_len: self.len_ = file_len - self.time
         else:        self.len_ = ''
      log.debug( 'creating index %s' % repr(self) )

   def __repr__(self):
      """Return a string used for debug logging."""
      return "'%s, %s'" % (self.file_, self.time)

   def __str__(self):
      """Return the TOC formated string representation of the
      :class:`TrackIndex` object."""
      out = []
      if self.cmd == self.DATA:
         return ''     # do not output to TOC
      if self.cmd in [self.AUDIO, self.PREAUDIO]:
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

   def _file_len(self,file_):
      """Returns the number of audio samples in the WAV file, *file_*.
      Called during __init__. If *file_* can not be opened, :data:`None`
      is returned.

      :param file_:  a file name string relative to the cwd referencing
                     a WAV file.
      :type file_:   str

      :rtype:        :class:`_TrackTime` of audio samples or
                     :data:`None`"""

      if not (file_ and os.path.exists(file_)):
         return None
      w = wave.open(file_)
      frames = w.getnframes() / (w.getframerate()/75)
      w.close()
      return _TrackTime(frames)


class _TrackTime(object):
   """
   Container class to represent the sample count or position in audio data.
   Allows mathematical operations to be easily performed on time positions.
   """
   #: Defines the number of audio *Frames Per Second*
   _FPS = 75
   #: Defines the number of *Seconds Per Minute*
   _SPM = 60
   #: Defines the number of audio *Frames Per Minute*
   _FPM = _FPS * _SPM

   #: :class:`tuple` that stores the minutes, seconds, and frames values. The
   #: combination of these values can be used to calculate the total frame
   #: count.
   _time = None

   def __init__(self, arg=None):
      """Initializes the :class:`_TrackTime` object, normalizing the input
      data.

      :param arg: Variable representation of the value of the
                  :class:`_TrackTime` object. The allowed formats are:
                     a. String in the format *MM:SS:FF*
                     b. Tuple in the format (M,S,F)
                     c. Integer of the total frame length
                     d. :data:`None`, object is initialized to 0 length
      :type arg: str, :class:`tuple`, int, :data:`None`"""
      if isinstance(arg,basestring):
         # extract time from string
         val = [int(x) for x in arg.split(':')]
         self._time = tuple(val)
      elif isinstance(arg,tuple):
         # assume arg is correct format
         self._time = arg
      elif isinstance(arg,(int,long)):
         # convert frame count to min,sec,frames
         min_,fr = divmod(arg, self._FPM)
         sec,fr = divmod(fr, self._FPS)
         self._time = (min_,sec,fr)
      else:
         # set time to '0:0:0' (zero)
         self._time = tuple([0]*3)

   def __repr__(self):
      """Return string value of the :class:`_TrackTime` in format
      *MM:SS:FF*."""
      return '%02d:%02d:%02d' % self._time

   def __ne__(self, other):
      """Return :data:`True` if objects are NOT equal."""
      return self._time != other._time

   def __eq__(self, other):
      """Return :data:`True` if objects are equal."""
      return self._time == other._time

   def __sub__(self, other):
      """Return result of *self* - *other*."""
      mn,sc,fr = map(lambda x,y: x-y, self._time, other._time)
      if fr<0: sc-=1; fr+=self._FPS
      if sc<0: mn-=1; sc+=self._SPM
      if mn<0: raise UnderflowError, \
         'Track time calculation resulted in a negative value'
      return _TrackTime((mn,sc,fr))

   @property
   def frames(self):
      """Convert min,sec,frame to total frames."""
      return sum( [x*y for x,y in
                     zip(self._time,[self._FPM,self._FPS,1]) ])

