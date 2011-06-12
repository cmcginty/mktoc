#  Copyright (c) 2011, Patrick C. McGinty
#
#  This program is free software: you can redistribute it and/or modify it
#  under the terms of the Simplified BSD License.
#
#  See LICENSE text for more details.
"""
   mktoc.wav
   ~~~~~~~~~

   Utility classes for search and modifying WAV audio files.

   The following are a list of the classes provided in this module:

   * :class:`WavFileCache`
   * :class:`WavOffsetWriter`
"""

import os
import sys
import re
import wave
import tempfile
import logging
import itertools as itr
import operator as op

from mktoc.base import *

__all__ = ['WavFileCache', 'WavOffsetWriter']

log = logging.getLogger('mktoc.wav')


##############################################################################
class WavFileCache(object):
   """
   Verifies the existence of a WAV file in the local file system.

   The class provides fuzzy logic name matching of cached results in the case
   that the specified file can not be found. The files system is only scanned
   once, and all lookups after the initial test come from the cache. The cache
   size is limited to prevent over aggressive file system access.
   """

   # list of WAV files found in the local file system.
   _data = None

   # base search path location.
   _src_dir = None

   # complied search object that can be used to match file name strings ending
   # with the '.wav' extension.
   _WAV_REGEX = re.compile(r'\.wav$', re.IGNORECASE)

   def __init__(self, _dir=os.curdir):
      """
      Initialize the class instance with the input :attr:`_dir` argument. If no
      argument is supplied it defaults to the current working dir.

      :param _dir:   Base path location to perform the WAV file search.
      :type _dir:    str

      .. Docuemnt private members
      .. automethod:: __call__
      """
      assert(_dir)
      self._src_dir = _dir

   def __call__(self, file_):
      """
      Search the cache for a fuzzy-logic match of the file name in
      :attr:`file_` parameter. This method will always return the exact file
      name if it exists before attempting fuzzy matches.

      :param file_:  File name to search for.
      :type file_:   str
      """
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
      fn_pat = sep + '.*' + re.escape(fn) + '.*'
      fn_pats = [fn_pat]
      # same as pat1, but replace spaces with underscores
      fn_us = fn.replace(' ','_')
      fn_pat = sep + '.*' + re.escape(fn_us) + '.*'
      fn_pats.append( fn_pat )
      # same as pat1, but replace underscores with spaces
      fn_us = fn.replace('_',' ')
      fn_pat = sep + '.*' + re.escape(fn_us) + '.*'
      fn_pats.append( fn_pat )
      file_regex = re.compile( '|'.join(set(fn_pats)), re.IGNORECASE)
      # search all WAV files using pattern 'file_regex'
      matchi = itr.imap( file_regex.search, self._get_cache() )
      # create tuple with input file and search results
      matches = itr.izip( self._get_cache(), matchi )
      matches = filter( op.itemgetter(1), matches )
      if len(matches) == 1:   # success if ONE match is found
         log.debug("--> FOUND '%s'" % matches[0][0])
         return matches[0][0]
      elif len(matches) == 0:
         raise FileNotFoundError, file_ # zero or multiple matches is an error
      else:
         raise TooManyFilesMatchError, (file_, [m[0] for m in matches])

   def _get_cache(self):
      """
      Helper function used to lookup the WAV file cache. The first call to this
      method will cause the creation of the cache.
      """
      if self._data is None:
         self._init_cache()
      return self._data

   def _init_cache(self):
      """
      Create a list of WAV files in the vicinity of the current working dir.
      The list is store in the object member '_data'.
      """
      self._data = []
      fc = 0
      log.debug("Initializing file cache @ '%s'", self._src_dir)
      for root, dirs, files in os.walk(self._src_dir):
         if fc > 1000: break     # only cache first n files
         fc += len(files)
         f_tup = zip( [root]*len(files), files )
         wav_files = [os.path.join(r,f) for r,f in f_tup \
                           if self._WAV_REGEX.search(f)]
         self._data.extend( wav_files )
      self._is_init = True
      log.debug('-> Found %d files:' % len(self._data) )
      map( lambda f: log.debug('--> %s' % f), self._data )


##############################################################################
class WavOffsetWriter(object):
   """
   Shift the audio data in a set of WAV files by a desired postive or negative
   sample offset.

   The module will never modify the input WAV files, and always write to either
   a new directory in the 'cwd' or in the :file:`/tmp` directory. The WAV files
   are treated as a set of data, in that, the direction of shift will cause
   audio sample data to be taken from either a previous or next WAV file. The
   shift in sample data will cause either the first or last WAV file to contain
   'sample count' of NULL samples.
   """

   # number of samples to copy for each cycle. This value affects the memory
   # required by this class and the frequency the progress bar is update.
   _COPY_SIZE = 256*1024

   # sample shift offset value.
   _offset = None

   # reference to a :class:`ProgressBar` instance to provide progress updates.
   _pb = None

   # string of the program name (i.e. mktoc) used when creating directories in
   # /tm.
   _progName = None

   def __init__(self, offset_samples, pb_class, pb_args):
      """
      :param offset_samples:  Sample shift value
      :type offset_samples:   int

      :param pb_class:  outputs status updates to the user. First argument of
                        the class init routine specifies the maximum value of
                        the progress bar and is calulated by this class.
      :type pb_class:   :class:`ProgressBar`

      :param pb_args:   Argument list used to initialize progress bar. However,
                        the first argument of the progress bar init routine is
                        calculated by this class.
      :type pb_args:    list

      .. Document private members
      .. automethod:: __call__
      """
      self._offset  = offset_samples
      self._pb_class = pb_class
      self._pb_args  = pb_args
      self._progName = os.path.basename( sys.argv[0] )

   def __call__(self, files, use_tmp_dir):
      """
      Initiate the WAV offsetting algorithm.

      New output files are written to either :file:`wav[+,-]n/` or
      :file:`/tmp/mktoc.[random]/`

      :param files:  WAV files read to apply the sample shifting process to.
      :type files:   list

      :param use_tmp_dir:  :data:`True` indicates new WAV files are created in
                           :file:`/tmp`.
      :type use_tmp_dir:   bool
      """
      # initialize the progress bar class, set the maximum progress bar value
      self._pb = self._pb_class( bar_max=self._get_total_samp(files),
                                 *self._pb_args)
      # set the dir name generation function, and create out_file list
      if not use_tmp_dir: outdir = self._get_new_name
      else              : outdir = self._get_tmp_name
      out_files = map( outdir, files )

      # positive offset correction, insert silence in first track,
      # all other tracks insert end data of previous track
      if self._offset > 0:
         offsetter_fnct = self._insert_prv_end
         # create a list of 'previous' file names
         f2_list = [None] + files[:-1]
      # negative offset correction, append silence to end of last track,
      # all other tracks append start data of next track
      elif self._offset < 0:
         offsetter_fnct = self._append_nxt_start
         # create a list of 'next' file names
         f2_list = files[1:] + [None]

      map( offsetter_fnct, out_files, files, f2_list )
      # return a list of the new files names
      return out_files

   def _append_nxt_start(self, out_fn, fn, nxt_fn):
      """Negative offset correction algorithm for a single WAV file.
      Copies the current WAV file data and then appends start of the
      next files WAV data into a new WAV file. The basic steps are:
         1) perform a positive 'n' sample seek into input WAV file.
         2) copy data from location to start of new WAV file until EOF
            of input.
         3) Either,
            a) open 'nxt_fn' WAV file and finish writing the last 'n'
               samples.
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
         self._write_frames(wav_out, data, bytes_p_samp)
      wav_in.close()
      # finally copy the remaining data from the next track, or silence
      if nxt_fn:
         # copy offset frame date from next file into new file
         wav_in = wave.open(nxt_fn)
         data = wav_in.readframes( abs(self._offset) )
         assert len(data) == offset_bytes
         self._write_frames(wav_out, data, bytes_p_samp)
      else:
         # write silence to end of last track
         self._write_frames(wav_out, '\x00'*offset_bytes, bytes_p_samp)
      # print the progress bar
      wav_in.close()
      wav_out.close()

   def _get_new_name(self, f):
      """Generates a new name a location to write 'wav[+,-]n/' WAV
      files."""
      dir_,name = os.path.split(f)
      new_dir = os.path.join(dir_, 'wav%+d' % self._offset)
      if not os.path.exists(new_dir):
         os.mkdir( new_dir )
      return os.path.join( new_dir, name)

   def _get_total_samp(self, files):
      """Helper function to return the total sample count of a list of
      WAV files. Used to set the ProgressBar 'max' value.

      Parameter:
         files : List of WAV files to read."""
      return sum(itr.imap( lambda f: wave.open(f).getnframes(), files))

   def _get_tmp_name(self, f):
      """Generates a new name a location to write
      '/tmp/mktoc.[random]/' WAV files."""
      if not hasattr(self, '_tmp_dir'):
         self._tmp_dir = tempfile.mkdtemp( prefix=self._progName+'.' )
      return os.path.join( self._tmp_dir, os.path.basename(f) )

   def _insert_prv_end(self, out_fn, fn, prv_fn):
      """Positive offset correction algorithm for a single WAV file.
      Inserts the end of the previous files WAV data and then copies
      the current WAV files data into a new WAV file. The basic steps
      are:
         1) Either,
            a) perform a positive (EOF - 'n') sample seek into
               'prv_fn' WAV file.
            b) if no 'prv_fn' use NULL data
         2) copy n samples of data to start of new WAV file.
         3) Open 'fn' WAV file and copy the full WAV file - 'n'
            samples to the output WAV.

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
         self._write_frames(wav_out, data ,bytes_p_samp)
         wav_in.close()
      else:    # insert silence if no previous file
         self._write_frames(wav_out ,'\x00'*offset_bytes, bytes_p_samp)
      # add original file data to output stream
      wav_in = wave.open( fn )
      samples = wav_in.getnframes() - self._offset
      while samples:
         data = wav_in.readframes( min(samples,self._COPY_SIZE) )
         samples -= len(data) / bytes_p_samp
         self._write_frames(wav_out, data, bytes_p_samp)
      wav_in.close()
      wav_out.close()

   def _write_frames(self, fh, data,bps):
      """Wrapper for writing data wav files. A secondary side effect
      is that each call udpates the progress bar."""
      fh.writeframes(data)
      self._pb += len(data) / bps      # update progress bar
      sys.stderr.write(str(self._pb))  # print the progress bar

