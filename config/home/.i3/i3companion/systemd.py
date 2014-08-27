#!/usr/bin/env python

from pluginmanager import notify
import wmiidbus # FIXME: Integrate into epoll event loop
import dbus

def get_logind():
    bus = wmiidbus.get_system_bus()
    proxy = bus.get_object('org.freedesktop.login1', '/org/freedesktop/login1')
    return dbus.Interface(proxy, 'org.freedesktop.login1.Manager')

def halt():
    get_logind().PowerOff(False)

def reboot():
    get_logind().Reboot(False)

def suspend():
    get_logind().Suspend(False)

def hibernate():
    get_logind().Hibernate(False)

def log_out():
	# FIXME: Do this directly from python rather than shelling out!
	import subprocess, sys
	subprocess.call(['i3-msg', 'exit'])
	sys.exit(0)

def switch_user():
    # This is display manager specific
    bus = wmiidbus.get_system_bus()
    proxy = bus.get_object('org.gnome.DisplayManager', '/org/gnome/DisplayManager/LocalDisplayFactory')
    iface = dbus.Interface(proxy, 'org.gnome.DisplayManager.LocalDisplayFactory')
    iface.CreateTransientDisplay()
    # TODO FIXME: Lock screen

# Defined as list of tuples to preserve order, converted to dict when needed
power_button_actions = [
		('OOPS WRONG BUTTON!', lambda : None),
		('Suspend to RAM', suspend),
		('Hibernate', hibernate),
		('Shut Down', halt),
		('Reboot', reboot),
		('Log Out', log_out),
		('Switch User', switch_user),
	]

def power_button():
	# FIXME: Do this asynchronousely
	import subprocess
	dmenu = subprocess.Popen(['dmenu', '-l', str(len(power_button_actions)), '-p',
		'Power Button Pressed! What would you like to do?'],
		stdin=subprocess.PIPE, stdout=subprocess.PIPE)
	dmenu.stdin.write('\n'.join(zip(*power_button_actions)[0]))
	dmenu.stdin.close()
	dmenu.wait()
	action = dmenu.stdout.read().strip()

	d = dict(power_button_actions)
	if action not in d:
		notify('Unrecognised action: %s' % action)
		return

	d[action]()

_inhibitfd = None
def inhibit_power_button():
    global _inhibitfd
    logind = get_logind()
    # Patches welcome if anyone doesn't want the lid switch inhibited
    _inhibitfd = logind.Inhibit('handle-power-key:handle-lid-switch', 'i3companion', 'i3companion handling power button', 'block').take()

def register_xf86_keys(keybinder):
	try:
		inhibit_power_button()
	except Exception as e:
		notify('%s inhibiting systemd handle-power-key & handle-lid-switch: %s' % \
				(e.__class__.__name__, str(e)), timeout = 5000)
                raise
	keybinder.bind_key(0, 'XF86_PowerOff', power_button)
