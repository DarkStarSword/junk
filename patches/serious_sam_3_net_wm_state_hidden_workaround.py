#!/usr/bin/env python

import Xlib.display

display = Xlib.display.Display()
display.intern_atom('_NET_WM_STATE_HIDDEN', False)
