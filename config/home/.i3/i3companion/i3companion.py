#!/usr/bin/env python

from pluginmanager import notify, notify_exception

try:
	from xkeybinder import XKeyBinder
except ImportError:
	notify('i3companion: Please install python-Xlib and python-xpyb', timeout=5000)
	raise

from eventloop import EventLoop
import config

def main():
	loop = EventLoop()
	keybinder = XKeyBinder(loop)

	config.activate_key_bindings(keybinder)

	loop.run()

if __name__ == '__main__':
	main()
