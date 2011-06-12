#  Copyright (c) 2011, Patrick C. McGinty
#
#  This program is free software: you can redistribute it and/or modify it
#  under the terms of the Simplified BSD License.
#
#  See LICENSE text for more details.
"""
   mktoc.fsm
   ~~~~~~~~~

   A finite state machine implementation.
"""

import operator as op


class NullStateException(Exception):
   """
   Exception thrown when :class:`StateMachine` has no state defined to handle
   the current input data.
   """


class StateMachine(object):
   """
   Base class for building a finite state machine.

   The state machine is controled by two externally provided data structures.

   .. attribute:: regex_obj

      A compiled :mod:`regex <re>` pattern instance that contains one or more
      named groups (i.e. ``(?P<name>...)``) sub-patterns.

   .. attribute:: match_handlers

      A :class:`dict` that maps a handler function to a group name returned by
      a successful match in the :data:`regex_obj` instance.

   .. warning::

      The :meth:`change_state` method must be run to initialize the state
      machine before the :class:`StateMachine` instance is called.

   .. Document private members
   .. automethod:: __call__
   """
   __regex_obj = None
   __match_handlers = None

   def __call__(self,lines):
      """
      For each line of text in :data:`lines`, a regex match is performed
      and a state handler function is called to finalize processing of the
      string.

      :param lines: Input data consumed by state machine
      :type  lines: list
      """
      for l in lines:
         match = self.__regex_obj.match(l)
         if match:
            match_name = match.lastgroup
            match_groups = [x for x in match.groups() if x]
            self.__match_handlers[match_name]( match_name, *match_groups)
         else:
            raise NullStateException(repr(l))

   def change_state(self,regex_obj=None,match_handlers=None):
      """
      Modifies the control flow of the state machine.

      Replaces the internal :data:`regex_obj` or :data:`match_handlers`.
      Using keywords, one paramter can be changed without effecting the other.

      :param regex_obj: Compiled regular expression object
      :type  regex_obj: :ref:`regex <re-objects>`

      :param match_handlers: handler functions map, keyed with
                             :data:`regex_obj` group name.
      :type  match_handlers: :class:`dict` of :func:`callable`\'s
      """
      if regex_obj:
         self.__regex_obj = regex_obj
      if match_handlers:
         self.__match_handlers = match_handlers

