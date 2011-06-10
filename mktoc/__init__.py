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
   .. Mktoc // (c) 2008, Patrick C. McGinty
   .. mktoc[@]tuxcoder[dot]com

   Mktoc simplifies the steps needed to create audio CD TOC files for the
   cdrdao CD burning program. For users familiar with ExactAudioCopy or CdrWin,
   TOC files are synonymous with CUE sheets. The primary goal of mktoc is to
   create TOC files using a previously generated CUE sheet.

   Features
   ========
   * Create a TOC file from a list of WAV files
   * Convert an ExactAudioCopy (EAC) CUE file to the TOC format that
     is usable by cdrdao.
   * Non-compliant CUE sheet support.
   * Support for various pregap methods.
   * Can create offset corrected WAV files for true 'bit-for-bit'
     accurate copies.
   * Fuzzy file name logic can correct common file name spelling
     variations.
   * Workaround known TOC file parsing bugs in cdrdao.

   Usage
   =====
   ::

      mktoc [OPTIONS] < CUE_FILE
      mktoc [OPTIONS] [[-f] CUE_FILE] [[-o] TOC_FILE]
      mktoc [OPTIONS] -w WAV_FILES [[-o] TOC_FILE]

   ``CUE_FILE`` must contain a valid CUE format. When ``*_FILE`` is not
   provided, the program will read from ``STDIN``. All output will be sent to
   ``STDOUT``.

   All attempts will be made to preserve any and all information from the input
   file. For any case where the CUE file contains unknown or bad values, the
   user will be notified on ``STDERR``.

   Options
   =======

   .. option:: --version

      show program's version number and exit

   .. option:: -h

      show help message and exit

   .. option:: --help

      show detailed usage instructions and exit

   .. option:: -a, --allow-missing-wav

      do not abort when WAV file(s) are missing, (experts only). It is possible
      when using this option that a bug in cdrdao will create a CD that ignores
      the pregap definitions in the TOC file.  Only use this option if the CUE
      file does not contain pregaps, or if you do not wish to retain the pregap
      information.

   .. option:: -c <WAV_OFFSET>, --offset-correction=<WAV_OFFSET>

      correct reader/writer offset by creating WAV file(s) shifted by
      WAV_OFFSET samples (original data is not modified)

   .. option:: -d, --debug

      enable debugging statements

   .. option:: -f <CUE_FILE>, --file=<CUE_FILE>

      specify the input CUE file to read

   .. option:: -m, --multi

      for safety, this option must be set when creating a mulit-session TOC
      file

   .. option:: -o <TOC_FILE>, --output=<TOC_FILE>

      specify the output TOC file to write

   .. option:: -t, --use-temp

      write offset corrected WAV files to /tmp directory

   .. option:: -w, --wave

      write a TOC file using list of WAV files

   .. option:: -z, --no-multi

      disable multi-session support; program assumes TOC will be written in
      single-session mode

   Examples
   ========
   1. Create a TOC file from a set of WAV files::

         mktoc -w *.wav

   2. Write a TOC file to :file:`toc_file.toc`, from a set of WAV files::

         mktoc -w *.wav toc_file.toc
         mktoc -w *.wav > toc_file.toc
         mktoc -w *.wav -o toc_file.toc

   3. Create a TOC file from a valid CUE file::

         mktoc cue_file.cue
         mktoc < cue_file.cue
         mktoc -f cue_file.cue

   4. Write a TOC file to :file:`toc_file.toc`, given an input CUE file::

         mktoc cue_file.cue toc_file.toc
         mktoc < cue_file.cue > toc_file.toc
         mktoc -f cue_file.cue -o toc_file.toc

   5. Tell mktoc to ignore missing WAV file errors. There is a potential that
      the result TOC file will cause cdrdao to loose pregap information during
      the burn process (see above)::

         mktoc -a cue_file.cue

   6. Adjust WAV files for a CD writer offset value. For example, if your CD
      writer has a -30 sample write offset, it can be corrected by offsetting
      the input WAV files by +30 samples. New WAV files will be placed in the
      working directory in a new dir called ``wav+30``::

         mktoc -c 30 < cue_file.cue

   7. Adjust WAV files for a CD writer offset value, but create new files in
      the :file:`/tmp directory`::

         mktoc -c 30 -t < cue_file.cue

   Contact
   =======

   E-mail
   ------
   |  mktoc[@]tuxcoder[dot]com

   Info
   ----
   |  http://mktoc.googlecode.com
   |  http://blog.tuxcoder.com
"""

__date__       = '$Date$'
__version__    = '$Revision$'


import sys
import mktoc.cmdline

if __name__ == '__main__':
   sys.exit(mktoc.cmdline.main())
