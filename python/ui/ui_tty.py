#!/usr/bin/env python
# vi:sw=2:ts=2:expandtab

from __future__ import print_function

import ui_null
import sys, tty

class ui_tty(object):
  # We don't implement a mainloop, but allow it to be queried, always returning
  # None for any query for easy compatibility with any code that implements
  # their own event loop and queries the mainloop (typically to get
  # file descriptors that need to be queries and input relayed):
  mainloop = ui_null.ui_null()

  # https://secure.wikimedia.org/wikipedia/en/wiki/ANSI_escape_code#CSI_codes
  # Refer to "SGR (Select Graphic Rendition) parameters"
  ttycolours = {
      'reset'          : '0',

      'bright'         : '1',
      #'faint'         : '2',
      #'italic'        : '3',
      'underline'      : '4',
      'blink'          : '5',
      #'rapid_blink'   : '6',
      'negative'       : '7',
      #'conceal'       : '8',
      #'crossed-out'   : '9',
      #10-19 - fonts
      #'fraktur'       : '20',
      #21 - bright/bold off; or double underline
      #22-29 - reset some things or reserved

      'black'          : '30',  'back_black'     : '40',
      'grey'         : '1;30',
      'red'            : '31',  'back_red'       : '41',
      'green'          : '32',  'back_green'     : '42',
      'yellow'         : '33',  'back_yellow'    : '43',
      'blue'           : '34',  'back_blue'      : '44',
      'magenta'        : '35',  'back_magenta'   : '45',
      'cyan'           : '36',  'back_cyan'      : '46',
      'white'          : '37',  'back_white'     : '47',
      # 38 - select 256 colour  # 38 - select 256 colour
      'default'        : '39',  'back_default'   : '49',
  }

  # I want to be able to call these without instantiating this class for the moment:
  @staticmethod
  def set_cbreak(fp=sys.stdin):
    old = None
    try:
      fileno = fp.fileno()
      old = tty.tcgetattr(fileno)
      tty.setcbreak(fileno)
    except: pass
    return old

  @staticmethod
  def restore_cbreak(old, fp=sys.stdin):
    if old is None: return
    fileno = fp.fileno()
    tty.tcsetattr(fileno, tty.TCSADRAIN, old)

  @staticmethod
  def reset():
    old = (tty.tcgetattr(sys.stdin.fileno()), tty.tcgetattr(sys.stdout.fileno()), tty.tcgetattr(sys.stderr.fileno()))
    import subprocess
    subprocess.call('reset')
    return old

  @staticmethod
  def restore(old):
    (i, o, e) = old
    tty.tcsetattr(sys.stdin.fileno(), tty.TCSADRAIN, i)
    tty.tcsetattr(sys.stdout.fileno(), tty.TCSADRAIN, o)
    tty.tcsetattr(sys.stderr.fileno(), tty.TCSADRAIN, e)

  @staticmethod
  def read_nonbuffered(prompt=None, echo=True, size=1, fp=sys.stdin):
    """
    Read size bytes from this file, which must be a tty (typically stdin),
    optionally displaying a prompt.
    """
    fileno = fp.fileno()
    if prompt:
      try:
        ui_tty._print(prompt, end='')
      except UnicodeDecodeError:
        ui_tty._print(prompt.encode('latin-1'), end='')
    old = ui_tty.set_cbreak(fp)
    try:
      while True:
        try:
          ch = fp.read(1)
        except IOError as e:
          if e.args[0] == 4: continue # Interrupted system call
          raise
        break
    finally:
      ui_tty.restore_cbreak(old, fp)
    if echo:
      try:
        ui_tty._print(ch)
      except UnicodeDecodeError:
        ui_tty._print(ch.encode('latin-1'))
    return ch

  def status(self, msg):
    ui_tty._print(msg)

  @staticmethod
  def confirm(prompt, default=None):
    ret = ''
    prompt = prompt + ' ' + {
        True:  '(Y,n)',
        False: '(y,N)',
        None:  '(y,n)',
        }[default] + ': '
    while ret not in ['y', 'n']:
      ret = ui_tty.read_nonbuffered(prompt).lower()
      if default is not None and ret in ['', '\n']:
        return default
    return ret == 'y'

  #--------WARNING: Unstable APIs below this line------------------------------

  @staticmethod
  def _print(msg='', sep=' ', end='\n', file=None):
    print(msg, sep=sep, end=end, file=file)

  @staticmethod
  def _sgr(colour):
    return '\x1b[%sm' % ';'.join([ ui_tty.ttycolours[x] for x in colour.split() ])

  @staticmethod
  def _ctext(colour, msg):
    return ui_tty._sgr(colour) + msg + ui_tty._sgr('reset')
  @staticmethod
  def _ctext_escape_len(colour='default'):
    return len(ui_tty._ctext(colour, ''))

  @staticmethod
  def _cprint(colour, msg='', sep=' ', end='\n', file=None):
    try:
      ui_tty._print(ui_tty._ctext(colour, msg), sep=sep, end=end, file=file)
    except KeyError:
      raise

  @staticmethod
  def _cconfirm(colour, prompt, default=None):
    try:
      return ui_tty.confirm(ui_tty._ctext(colour, prompt), default=default)
    except KeyError:
      raise
