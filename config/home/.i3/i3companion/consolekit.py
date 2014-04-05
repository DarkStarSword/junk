#!/usr/bin/env python

from pluginmanager import notify
import wmiidbus # FIXME: Integrate into epoll event loop
import dbus

def get_consolekit():
	bus = wmiidbus.get_system_bus()
	proxy = bus.get_object('org.freedesktop.ConsoleKit', '/org/freedesktop/ConsoleKit/Manager')
	return dbus.Interface(proxy, 'org.freedesktop.ConsoleKit.Manager')

def halt():
	get_consolekit().Stop()

def reboot():
	get_consolekit().Restart()

def suspend():
	import upower
	upower.suspend()

def hibernate():
	import upower
	upower.hibernate()

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

def fake_gnome_settings_daemon():
	import subprocess, sys, os
	# FIXME: path will be wrong if we are a submodule
	# FIXME: Check if fake gnome-settings-daemon has been built
	path = os.path.join(os.path.dirname(sys.argv[0]), 'gnome-settings-daemon')
	subprocess.Popen(path, stdout=open('/dev/null', 'w'),
			stdin=subprocess.PIPE, close_fds=True)

	# Need to trick this line in /usr/share/acpi-support/policy-funcs:
	# DBusSend gnome-settings-daemon org.gnome.SettingsDaemon
	#   /org/gnome/SettingsDaemon/Power
	#   org.freedesktop.DBus.Introspectable.Introspect | grep -q 'interface
	#   name="org.gnome.SettingsDaemon.Power"'

	class FakeGnomeSettings(dbus.service.Object):
		def __init__(self, bus):
			bus_name = dbus.service.BusName('org.gnome.SettingsDaemon', bus=bus)
			dbus.service.Object.__init__(self, bus_name, '/org/gnome/SettingsDaemon/Power')

		@dbus.service.method(dbus_interface='org.gnome.SettingsDaemon.Power')
		def FakeGnomeSettingsDaemon(self):
			pass

	bus = wmiidbus.get_session_bus()
	fake = FakeGnomeSettings(bus)

def register_xf86_keys(keybinder):
	try:
		fake_gnome_settings_daemon()
	except Exception as e:
		notify('%s trying to start fake "gnome-settings-daemon": %s.  Power button will not be caught!' % \
				(e.__class__.__name__, str(e)), timeout = 5000)
		return
	keybinder.bind_key(0, 'XF86_PowerOff', power_button)

if __name__ == '__main__':
	fake_gnome_settings_daemon()
