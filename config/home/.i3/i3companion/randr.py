#!/usr/bin/env python

import xcb.xproto
import xcb.randr
import struct

from pluginmanager import notify

def adj_backlight(delta):
	# FIXME: Refactor this function - it got nasty!
	conn = xcb.connect()
	root = conn.get_setup().roots[0].root
	randr = conn(xcb.randr.key)
	# TODO: Check randr.QueryVersion
	# TODO: Don't create if it atom doesn't exist & handle
	backlight_atoms = [ conn.core.InternAtom(False, len(name), name).reply().atom \
				for name in ('Backlight', 'BACKLIGHT') ]
	resources = randr.GetScreenResources(root).reply()
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
				val = backlight_prop.reply().data[0]
				new = max(bmin, min(bmax, val + delta))
				if new != val:
					val = new
					randr.ChangeOutputProperty(output,
							backlight_atom,
							xcb.xproto.Atom.INTEGER,
							32,
							xcb.xproto.PropMode.Replace,
							1, [val])
				yield(name, 100 * (val - bmin) / bmax)
				conn.flush()
				break
			except xcb.xproto.BadName:
				continue

def notify_brightness(input):
	for (name, brightness) in input:
		notify('%s: %i%%' % (name, brightness), key='backlight')

def raise_brightness():
	return notify_brightness(adj_backlight(+1))

def lower_brightness():
	return notify_brightness(adj_backlight(-1))

def register_xf86_keys(keybinder):
	keybinder.bind_key(0, 'XF86_MonBrightnessUp', raise_brightness)
	keybinder.bind_key(0, 'XF86_MonBrightnessDown', lower_brightness)

if __name__ == '__main__':
	for (name, brightness) in adj_backlight(0):
		print '%s: %i%%' % (name, brightness)
