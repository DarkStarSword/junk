#!/usr/bin/env python

import xcb.xproto
import xcb.randr
import struct
import math
import time

from pluginmanager import notify

# XXX: Can I get notified of this being updated instead of timing it out?
_resources = None
_resources_timestamp = None
def get_resources(conn, randr):
	global _resources
	global _resources_timestamp
	t = time.time()
	if _resources is None or _resources_timestamp > t or t - _resources_timestamp > 5:
		root = conn.get_setup().roots[0].root
		_resources = randr.GetScreenResources(root).reply()
		_resources_timestamp = t
	return _resources

def adj_backlight(delta):
	# FIXME: Refactor this function - it got nasty!
	conn = xcb.connect()
	randr = conn(xcb.randr.key)
	# TODO: Check randr.QueryVersion
	# TODO: Don't create if it atom doesn't exist & handle
	backlight_atoms = [ conn.core.InternAtom(False, len(name), name).reply().atom \
				for name in ('Backlight', 'BACKLIGHT') ]
	resources = get_resources(conn, randr)
	cookies = []

	for output in resources.outputs:
		cookies.append((
				output,
				randr.GetOutputInfo(output, resources.timestamp),
				[],
			))
		for backlight_atom in backlight_atoms:
			cookies[-1][-1].append((
					backlight_atom,
					randr.QueryOutputProperty(output, backlight_atom),
					randr.GetOutputProperty(output, backlight_atom,
						xcb.xproto.Atom.INTEGER, 0,
						struct.calcsize('L'), 0, 0)
				))

	for (output, info_cookie, backlight_cookies) in cookies:
		name = ''.join(map(chr, info_cookie.reply().name))
		for (backlight_atom, backlight_query, backlight_prop) in backlight_cookies:
			try:
				(bmin, bmax) = list(backlight_query.reply().validValues)
				val = backlight_prop.reply().data

                                # This seems wrong - why am I getting an array
                                # of four bytes instead of python-xcb giving me
                                # an Integer?
                                #
                                # XXX: I'm assuming this is little-endian,
                                # given that X is supposed to be a network
                                # protocol so this has to be well defined, and
                                # the values I'm seeing are little-endian
                                val = struct.unpack('<I', struct.pack('4B', *val))[0]

                                if delta:
                                    delta = (delta * (bmax - bmin) / 100) or math.copysign(1, delta)
				new = max(bmin, min(bmax, val + delta))
				if new != val:
					val = new
                                        valb = struct.unpack('4B', struct.pack('<I', new))
					randr.ChangeOutputProperty(output,
							backlight_atom,
							xcb.xproto.Atom.INTEGER,
							32,
							xcb.xproto.PropMode.Replace,
							1, valb)
				yield(name, 100 * (val - bmin) / bmax)
				conn.flush()
				break
			except xcb.xproto.BadName:
				continue
	conn.disconnect()

def notify_brightness(input):
	for (name, brightness) in input:
		notify('%s: %i%%' % (name, brightness), key='backlight')

def raise_brightness():
	return notify_brightness(adj_backlight(+5))

def lower_brightness():
	return notify_brightness(adj_backlight(-5))

def register_xf86_keys(keybinder):
	keybinder.bind_key(0, 'XF86_MonBrightnessUp', raise_brightness)
	keybinder.bind_key(0, 'XF86_MonBrightnessDown', lower_brightness)

if __name__ == '__main__':
	for (name, brightness) in adj_backlight(0):
		print '%s: %i%%' % (name, brightness)
