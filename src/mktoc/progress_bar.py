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

__date__ = '$Date$'
__version__ = '$Revision$'

import time

from mktoc.base import *

__all__ = ['ProgressBar']


class ProgressBar( object ):
   """"""
   def __init__(self, notice_txt):
      self._notice_txt = notice_txt
      self._size  = 0
      self.max_   = 0           # default max value

   def __iadd__(self, other):
      """"""
      self._size += min(other, self.max_ - self._size)
      return self

   def __str__(self):
      """"""
      if not self.max_:
         raise Exception, "You must initialize ProgressBar.max_ first"
      if not hasattr(self,'_start_time'):
         self._start_time = time.time()
         time_dif = 0
      else:
         time_dif = time.time() - self._start_time    # compute time from start
      percent = float(self._size) / self.max_ * 100
      if time_dif:
         rate = self._size / time_dif      # calculate sample/sec
         # estimate time left
         remain_time = (self.max_ - self._size) / rate
         remain_str = '\tETA [%d:%02d]' % divmod(remain_time,60)
      else:
         remain_str = '\tETA [?:??]'
      return '%s %3d%% %s\r' % (self._notice_txt, percent, remain_str)

