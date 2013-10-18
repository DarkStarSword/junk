#!/usr/bin/env python

from pluginmanager import notify

import wmiidbus # FIXME: Integrate into epoll event loop
import dbus

def get_upower():
	bus = wmiidbus.get_system_bus()
	upower_proxy = bus.get_object('org.freedesktop.UPower', '/org/freedesktop/UPower')
	return dbus.Interface(upower_proxy, 'org.freedesktop.UPower')

def suspend():
	get_upower().Suspend()

def hibernate():
	get_upower().Hibernate()

def adj_kbd_backlight(delta):
	bus = wmiidbus.get_system_bus()
	kbd_backlight_proxy = bus.get_object('org.freedesktop.UPower', '/org/freedesktop/UPower/KbdBacklight')
	kbd_backlight = dbus.Interface(kbd_backlight_proxy, 'org.freedesktop.UPower.KbdBacklight')

	val = kbd_backlight.GetBrightness()
	kmax = kbd_backlight.GetMaxBrightness()

	new = max(0, min(kmax, val + delta * kmax))
	if new != val:
		val = new
		kbd_backlight.SetBrightness(val)
	return 100 * val / kmax

def notify_kbd_backlight(val):
	notify('Keyboard Backlight: %i%%' % val, key = 'Keyboard Backlight')

def raise_kbd_backlight():
	return notify_kbd_backlight(adj_kbd_backlight(+0.08))

def lower_kbd_backlight():
	return notify_kbd_backlight(adj_kbd_backlight(-0.08))

def register_xf86_keys(keybinder):
	keybinder.bind_key(0, 'XF86_KbdBrightnessUp', raise_kbd_backlight)
	keybinder.bind_key(0, 'XF86_KbdBrightnessDown', lower_kbd_backlight)

if __name__ == '__main__':
	print '%i%%' % adj_kbd_backlight(0)
