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
import sys
import re
import wave
import tempfile

from mktoc_global import *

WAV_REGEX = re.compile(r'\.wav$', re.IGNORECASE)

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

   def __init__(self, offset_samples, progress_bar):
      """"""
      self._offset  = offset_samples
      self._pb = progress_bar
      self._progName = os.path.basename( sys.argv[0] )

   def execute(self, files, use_tmp_dir):
      """"""
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
      """Negative offset correction"""
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
      """"""
      dir_,name = os.path.split(f)
      new_dir = os.path.join(dir_, 'wav%+d' % self._offset)
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
         self._tmp_dir = tempfile.mkdtemp( prefix=self._progName+'.' )
      return os.path.join( self._tmp_dir, os.path.basename(f) )

   def _insert_prv_end(self, out_fn, fn, prv_fn):
      """Positive offset correction"""
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

