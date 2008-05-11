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
Module for mktoc that can holds utility functions for search and modifying WAV
audio files. The available object classes are:

   WavFileCache
      Verifies the existence of a WAV file in the local file system. The class
      provides fuzzy logic name matching of cached results in the case that the
      specified file can not be found.

   WavOffsetWriter
      Shift the audio data in a set of WAV files by a desired postive or
      negative sample offset.
"""

__date__    = '$Date$'
__version__ = '$Revision$'

import os
import sys
import re
import wave
import tempfile
import logging

from mktoc.base import *

__all__ = ['WavFileCache', 'WavOffsetWriter']

log = logging.getLogger('mktoc.wav')


class WavFileCache(object):
   """Verifies the existence of a WAV file in the local file system. The class
   provides fuzzy logic name matching of cached results in the case that the
   specified file can not be found. The files system is only scanned once, and
   all lookups after the initial test come from the cache. The cache size is
   limited to prevent over aggressive file system access.

   Constants:
      _WAV_REGEX
         A complied search object that can be used to match file name strings
         ending with the '.wav' extension.

   Private Data Members:
      _data    : String list of WAV files found in the local file system.

      _src_dir : String that stores the base search path location."""

   _WAV_REGEX = re.compile(r'\.wav$', re.IGNORECASE)

   def __init__(self, _dir=os.curdir):
      """Initialize the internal member _src_dir with the input '_dir'
      argument. If no argument is supplied it defaults to the current working
      dir."""
      self._src_dir = _dir

   def lookup(self, file_):
      """Search the cache for a fuzzy-logic match of the file name in 'file_'
      parameter. This method will always return the exact file name if it
      exists before attempting fuzzy matches.

      Parameter:
         file_    : String of the file name to search for."""
      log.debug("looking for file '%s'",file_)
      tmp_name = file_
      # convert a DOS file path to Linux
      tmp_name = tmp_name.replace('\\','/')
      # base case: file exists, and is has a 'WAV' extension
      if self._WAV_REGEX.search(tmp_name) and os.path.exists(tmp_name):
         log.debug('-> FOUND\n'+'-'*5)
         return file_       # return match
      # case 2: file is locatable in path by stripping directories
      fn = os.path.basename(tmp_name)     # strip leading path
      fn = os.path.splitext(fn)[0]        # strip extension
      fn = fn.strip()                     # strip any whitespace
      log.debug("-> looking for file '%s'", os.sep + fn + '.wav')
      # escape any special characters in the file, and the '$' prevents
      # matching if any extra chars come after the name
      sep = re.escape(os.sep)
      dot_wav = re.escape('.wav')
      fn_pat = sep + '.*' + re.escape(fn) + '.*' + dot_wav + '$'
      fn_pats = [fn_pat]
      # same as pat1, but replace spaces with underscores
      fn_us = fn.replace(' ','_')
      fn_pat = sep + '.*' + re.escape(fn_us) + '.*' + dot_wav + '$'
      fn_pats.append( fn_pat )
      # same as pat1, but replace underscores with spaces
      fn_us = fn.replace('_',' ')
      fn_pat = sep + '.*' + re.escape(fn_us) + '.*' + dot_wav + '$'
      fn_pats.append( fn_pat )
      file_regex = re.compile( '|'.join(fn_pats), re.IGNORECASE)
      match = None
      for f in self._get_cache():
         log.debug("--> comparing file '%s'",f)
         if file_regex.search(f):   # if match was found
            log.debug('--> FOUND\n'+'-'*5)
            if match is not None: # exception if there was more than 1 match
               raise FileNotFoundError, file_
            match = f               # save match
      if match is not None: return match
      raise FileNotFoundError, file_

   def _get_cache(self):
      """Helper function used to lookup the WAV file cache. The first call to
      this method will cause the creation of the cache."""
      if not hasattr(self,'_data'):
         self._init_cache()
      return self._data

   def _init_cache(self):
      """Create a list of WAV files in the vicinity of the current working
      dir. The list is store in the object member '_data'."""
      self._data = []
      fc = 0
      for root, dirs, files in os.walk(self._src_dir):
         if fc > 1000: break     # only cache first n files
         fc += len(files)
         f_tup = zip( [root]*len(files), files )
         wav_files = [os.path.join(r,f) for r,f in f_tup \
                           if self._WAV_REGEX.search(f)]
         self._data.extend( wav_files )
      self._is_init = True


##############################################################################
class WavOffsetWriter(object):
   """Shift the audio data in a set of WAV files by a desired postive or
   negative sample offset. The module will never modify the input WAV files,
   and always write to either a new directory in the 'cwd' or in the '/tmp'
   directory. The WAV files are treated as a set of data, in that the direction
   of shift will cause audio sample data to be taken from either a previous or
   next WAV file. The shift in sample data will cause either the first or last
   WAV file to contain 'sample count' of NULL samples.

   Constants:
      _COPY_SIZE
         Specifies the number of samples to copy for each cycle. This value
         affects the memory required by this class and the frequency the
         progress bar is update.

   Private Data Members:
      _offset
         The sample shift offset value.

      _pb
         Reference to a ProgressBar object to provide progress updates.

      _progName
         String of the program name (i.e. mktoc) used when creating directories
         in /tmp.
   """
   _COPY_SIZE = 256*1024

   def __init__(self, offset_samples, progress_bar):
      """Initialize private data members.

      Parameters:
         offset_samples    : The sample shift value assigned to '_offset'.

         progress_bar      : Reference to a ProgressBar object used to give
                             status updates to the user."""
      self._offset  = offset_samples
      self._pb = progress_bar
      self._progName = os.path.basename( sys.argv[0] )

   def execute(self, files, use_tmp_dir):
      """Initiate the WAV offsetting algorithm. New output files are written
      to either 'wav[+,-]n/' or '/tmp/mktoc.[random]/'

      Parameters:
         files       : A list of WAV files read to apply the sample shifting
                       process to.

         use_tmp_dir : True/False, True indicates new WAV files are created in
                       /tmp."""
      # set the maximum progress bar value
      self._pb.max_ = self._get_total_samp( files )
      # positive offset correction, insert silence in first track,
      # all other tracks insert end data of previous track
      if self._offset > 0:
         # create a list of 'previous' file names
         f2_list = [None] + files[:-1]
         offsetter_fnct = self._insert_prv_end

      # negative offset correction, append silence to end of last track,
      # all other tracks append start data of next track
      elif self._offset < 0:
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
      """Negative offset correction algorithm for a single WAV file. Copies the
      current WAV file data and then appends start of the next files WAV data
      into a new WAV file. The basic steps are:
         1) perform a positive 'n' sample seek into input WAV file.
         2) copy data from location to start of new WAV file until EOF of
            input.
         3) Either,
            a) open 'nxt_fn' WAV file and finish writing the last 'n' samples.
            b) pad the new WAV file with n samples of NULL data.

      Parameters:
         out_fn   : String of output WAV file name.

         fn       : String of intput WAV file name.

         nxt_fn   : String of N+1 input WAV file name."""
      wav_out = wave.open(out_fn, 'w')
      wav_in = wave.open(fn)
      # setup the output parameters
      bytes_p_samp = wav_in.getsampwidth() * wav_in.getnchannels()
      offset_bytes = abs(self._offset) * bytes_p_samp
      wav_out.setparams( wav_in.getparams() )
      # seek ahead sample offset amount
      wav_in.setpos( abs(self._offset) )
      # copy all frame date from 1st file into new file
      while True:
         data = wav_in.readframes(self._COPY_SIZE)
         if len(data) == 0: break
         wav_out.writeframes( data )
         self._pb += len(data) / bytes_p_samp
         sys.stderr.write(str(self._pb))
         del data
      wav_in.close()
      # finally copy the remaining data from the next track, or silence
      if nxt_fn:
         # copy offset frame date from next file into new file
         wav_in = wave.open(nxt_fn)
         data = wav_in.readframes( abs(self._offset) )
         assert len(data) == offset_bytes
         wav_out.writeframes( data )
         self._pb += len(data) / bytes_p_samp
      else:
         # write silence to end of last track
         data = '\x00' * offset_bytes
         wav_out.writeframes( data )
         self._pb += len(data) / bytes_p_samp
      # print the progress bar
      sys.stderr.write(str(self._pb))
      del data
      wav_in.close()
      wav_out.close()

   def _get_new_name(self, f):
      """Generates a new name a location to write 'wav[+,-]n/' WAV files."""
      dir_,name = os.path.split(f)
      new_dir = os.path.join(dir_, 'wav%+d' % self._offset)
      if not os.path.exists(new_dir):
         os.mkdir( new_dir )
      return os.path.join( new_dir, name)

   def _get_total_samp(self, files):
      """Helper function to return the total sample count of a list of WAV
      files. Used to set the ProgressBar 'max' value.

      Parameter:
         files : List of WAV files to read."""
      count = 0
      for f in files:
         count += wave.open(f).getnframes()
      return count

   def _get_tmp_name(self, f):
      """Generates a new name a location to write '/tmp/mktoc.[random]/' WAV
      files."""
      if not hasattr(self, '_tmp_dir'):
         self._tmp_dir = tempfile.mkdtemp( prefix=self._progName+'.' )
      return os.path.join( self._tmp_dir, os.path.basename(f) )

   def _insert_prv_end(self, out_fn, fn, prv_fn):
      """Positive offset correction algorithm for a single WAV file. Inserts
      the end of the previous files WAV data and then copies the current WAV
      files data into a new WAV file. The basic steps are:
         1) Either,
            a) perform a positive (EOF - 'n') sample seek into 'prv_fn' WAV
               file.
            b) if no 'prv_fn' use NULL data
         2) copy n samples of data to start of new WAV file.
         3) Open 'fn' WAV file and copy the full WAV file - 'n' samples to
            the output WAV.

      Parameters:
         out_fn   : String of output WAV file name.

         fn       : String of intput WAV file name.

         prv_fn   : String of N-1 input WAV file name."""
      wav_out = wave.open(out_fn, 'w')
      wav_in = wave.open(fn)
      # setup the output parameters
      bytes_p_samp = wav_in.getsampwidth() * wav_in.getnchannels()
      offset_bytes = self._offset * bytes_p_samp
      wav_out.setparams( wav_in.getparams() )
      wav_in.close()
      # if previous file exists, insert end of stream to new file
      if prv_fn:
         wav_in = wave.open(prv_fn)
         pos = wav_in.getnframes() - self._offset   # seek position
         wav_in.setpos( pos ) # seek to EOF - offset
         data = wav_in.readframes( self._offset )
         assert len(data) == offset_bytes
         wav_out.writeframes( data )
         self._pb += len(data) / bytes_p_samp
         wav_in.close()
      else:    # insert silence if no previous file
         data = '\x00' * offset_bytes
         wav_out.writeframes( data )
         self._pb += len(data)/bytes_p_samp
      # print the progress bar
      sys.stderr.write(str(self._pb))
      # add original file data to output stream
      wav_in = wave.open( fn )
      samples = wav_in.getnframes() - self._offset
      while samples:
         data = wav_in.readframes( min(samples,self._COPY_SIZE) )
         samples -= len(data) / bytes_p_samp
         wav_out.writeframes( data )
         self._pb += len(data) / bytes_p_samp
         sys.stderr.write(str(self._pb))
         del data
      wav_in.close()
      wav_out.close()

