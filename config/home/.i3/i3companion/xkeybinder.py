#!/usr/bin/env python

# Yes, I'm using two X libraries. Yes, I connect to the X server twice.

# python-Xlib is simpler, but is impossible to integrate into a poll/select
# event loop since the underlying socket always has data waiting to be read,
# yet calling next_event() blocks.

# AFAICT xcb is missing some important functions, like keysym_to_keycode.

missing_keysyms = {
	# These are missing from python-Xlib's definitions
	'XF86_AudioMicMute'   : 0x1008FFB2, # Mute the Mic from the system
	'XF86_BackForward'    : 0x1008FF3F, # ???
	'XF86_Hibernate'      : 0x1008FFA8, # Sleep to disk
	'XF86_LogGrabInfo'    : 0x1008FE25, # print all active grabs to log
	'XF86_LogWindowTree'  : 0x1008FE24, # print window tree to log
	'XF86_ModeLock'       : 0x1008FF01, # Mode Switch Lock
	'XF86_Suspend'        : 0x1008FFA7, # Sleep to RAM
	'XF86_TouchpadOff'    : 0x1008FFB1, # The touchpad got switched off
	'XF86_TouchpadOn'     : 0x1008FFB0, # The touchpad got switched on
	'XF86_TouchpadToggle' : 0x1008FFA9, # Toggle between touchpad/trackstick
}

class XKeyBinder(object):
	import xcb.xproto   # For events (python-Xlib socket is problematic with poll())
	import Xlib.display # For looking up keysyms (xcb is missing this functionality)
	import Xlib.XK
	Xlib.XK.load_keysym_group('xf86')

	from xcb.xproto import ModMask
	Control = ModMask.Control
	Shift = ModMask.Shift
	Alt = ModMask._1
	Win = ModMask._4

	extra_modifiers = (0, ModMask.Lock, # Caps lock
			      ModMask._2,   # Numlock
			      ModMask.Lock | ModMask._2)

	def __init__(self, event_loop):
		self.loop = event_loop
		self.bindings = {}
		self.keysyms = missing_keysyms
		self.xcb_conn = self.xcb.connect()
		self.xcb_root = self.xcb_conn.get_setup().roots[0].root
		self.loop.register(self.xcb_conn.get_file_descriptor(), self.handle_event)

		# XXX: Because python-Xlib prints
		# 'Xlib.protocol.request.QueryExtension' to stdout
		import sys, StringIO
		(tmp, sys.stdout) = (sys.stdout, StringIO.StringIO())
		# XXX: Would be nice to drop this altogether:
		self.xlib_conn = self.Xlib.display.Display()
		sys.stdout = tmp

	def __del__(self):
		self.loop.unregister(self.xcb_conn.get_file_descriptor())
		self.xcb_conn.disconnect()
                self.xlib_conn.close()

	def bind_key(self, modifiers, key, func, args=(), kwargs={}):
		keycodes = [(key, modifiers)]
		if isinstance(key, str):
			if key in self.keysyms:
				keysym = self.keysyms[key]
			else:
				keysym = self.Xlib.XK.string_to_keysym(key)
				if keysym == 0:
					raise KeyError(key)
			# print 'keysym: ', hex(keysym)
			keycodes = self.xlib_conn.keysym_to_keycodes(keysym)
			# print 'keycodes: ', keycodes
			if keycodes == []:
				raise KeyError(key)
			keycodes = set([ (k, (1 << m >> 1) | modifiers) for (k, m) in keycodes ])
			# print 'keycodes: ', keycodes

		for (keycode, base_modifier) in keycodes:
			for modifier in map(lambda extra: base_modifier | extra, self.extra_modifiers):
				# print 'binding %4i %.4x' % (keycode, modifier)
				self.xcb_conn.core.GrabKey(0, self.xcb_root,
							   modifier, keycode,
							   self.xcb.xproto.GrabMode.Sync,
							   self.xcb.xproto.GrabMode.Async)
				self.bindings[(keycode, modifier)] = \
						(func, args, kwargs)
		self.xcb_conn.flush()

	def handle_event(self):
		while True:
			event = self.xcb_conn.poll_for_event()
			if event is None:
				return

			if not isinstance(event, self.xcb.xproto.KeyPressEvent):
				continue

			(keycode, modifiers) = (event.detail, event.state)
			try:
				(func, args, kwargs) = self.bindings[(keycode, modifiers)]
			except KeyError:
				continue

			func(*args, **kwargs)

if __name__ == '__main__':
	from eventloop import EventLoop
	loop = EventLoop()
	bindings = XKeyBindings(loop)

	def foo():
		print 'FOO!!!'
	def bar():
		print 'BAR!!!'
	def baz():
		print 'BAZ!!!'
		loop.stop()
	bindings.bind_key(0, 'parenleft', foo)
	bindings.bind_key(0, 'parenright', bar)
	bindings.bind_key(0, 'Escape', baz)
	loop.run()
