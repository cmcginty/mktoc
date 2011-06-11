#  Copyright (c) 2011, Patrick C. McGinty
#
#  This program is free software: you can redistribute it and/or modify it
#  under the terms of the Simplified BSD License.
#
#  See LICENSE text for more details.
"""
   mktoc.progress_bar
   ~~~~~~~~~~~~~~~~~~

   Module for mktoc that prints a progress indication.

   The default usage is to prompt the user when an operation is running that
   the user must wait for. The following object classes are:
"""

__date__    = '$Date$'
__version__ = '$Revision$'

import time

from mktoc.base import *

__all__ = ['ProgressBar']


##############################################################################
class ProgressBar( object ):
   """
   Creates a progress bar string to be printed by the calling function.
   """

   #: The maximum input input value expected by the progress bar. This value
   #: should be set before trying to print the progress bar. All percentage
   #: calculations are based from this value. It is OK to update this value as
   #: many times as needed, however it might confuse the user.
   bar_max = None

   # String to contain a message printed alongside the progress bar.
   _notice_text = None

   # The total integer count of the 'progress'. This value is modified by the
   # overloaded '+=' operator. This value can never go above 'bar_max'.
   _size = None

   def __init__(self, notice_txt, bar_max=0):
      """
      Initialize object defaults.

      :param notice_txt:   Message printed alongside the progress bar.
      :type notice_txt:    str

      :param bar_max:   Maximum size of the progress bar class.
      :type bar_max:    int
      """
      self._notice_txt = notice_txt
      self._size = 0
      self.bar_max = bar_max

   def __iadd__(self, other):
      """+= operator that increments the current state of the progress bar. The
      input value can be of any range, but the progress bar value will be fixed
      at 'bar_max'."""
      self._size += min(other, self.bar_max - self._size)
      return self

   def __str__(self):
      """Returns a progress bar string."""
      if not self.bar_max:
         raise Exception("You must initialize ProgressBar.bar_max first")
      if not hasattr(self,'_start_time'):
         self._start_time = time.time()
         time_dif = 0
      else:
         time_dif = time.time() - self._start_time    # compute time from start
      percent = float(self._size) / self.bar_max * 100
      if time_dif:
         rate = self._size / time_dif      # calculate sample/sec
         # estimate time left
         remain_time = (self.bar_max - self._size) / rate
         remain_str = '\tETA [%d:%02d]' % divmod(remain_time,60)
      else:
         remain_str = '\tETA [?:??]'
      return '%s %3d%% %s\r' % (self._notice_txt, percent, remain_str)

