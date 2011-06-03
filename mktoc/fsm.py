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

   The state machine is controled by two externally provided data structures:

      regex_obj : a compiled RegEx pattern instance that contains one or more
                  named groups (i.e. `(?P<name>...)`) sub-patterns.

      match_handlers : a ;type:`dict` that maps a handler function to a group
                       name returned by a successful match in the regex_obj
                       instance.

   The :method:`change_state` method must be run to initialize the state
   machine before the :class:`StateMachine` instance is called.
   """
   __regex_obj = None
   __match_handlers = None

   def __call__(self,lines):
      """
      Implements the state machine processing logic.
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

      Replaces the internal :param:`regex_obj` or :param:`match_handlers`.
      Using keywords, one paramter can be changed without effecting the other.
      """
      if regex_obj:
         self.__regex_obj = regex_obj
      if match_handlers:
         self.__match_handlers = match_handlers

