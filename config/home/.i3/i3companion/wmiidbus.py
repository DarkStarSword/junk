#!/usr/bin/env python

# TODO: Throw away threading and integrate into epoll event loop

import dbus
import dbus.service
import threading

_system_bus = None
_session_bus = None
_main_loop = None
_bus_loop = None
_thread = None

_system_bus_lock = threading.Lock()
def get_system_bus(start_thread=True):
	global _system_bus

	# TODO: Check if still connected
	if _system_bus is not None:
		return _system_bus
	with _system_bus_lock:
		if _system_bus is None:
			(main_loop, bus_loop) = get_main_loop()
			_system_bus = dbus.SystemBus(mainloop = bus_loop)
		if start_thread:
			start_main_loop()
		return _system_bus

_session_bus_lock = threading.Lock()
def get_session_bus(start_thread=True):
	global _session_bus

	if _session_bus is not None and _session_bus.get_is_connected():
		return _session_bus
	with _session_bus_lock:
		if _session_bus is None:
			(main_loop, bus_loop) = get_main_loop()
			_session_bus = dbus.SessionBus(mainloop = bus_loop)
		if start_thread:
			start_main_loop()
		return _session_bus

_main_loop_lock = threading.Lock()
def get_main_loop():
	global _main_loop, _bus_loop

	if _main_loop is not None:
		return (_main_loop, _bus_loop)
	with _main_loop_lock:
		if _main_loop is not None:
			return (_main_loop, _bus_loop)

		from dbus.mainloop.glib import DBusGMainLoop
		import gobject

		_bus_loop = DBusGMainLoop(set_as_default=True)
		gobject.threads_init()

		from dbus import glib
		glib.threads_init()

		_main_loop = gobject.MainLoop()
		return (_main_loop, _bus_loop)

def _main_loop_thread():
	"""
	Start the glib main loop. Should be in it's own thread.
	"""
	(main_loop, bus_loop) = get_main_loop()
	main_loop.run()

_thread_lock = threading.Lock()
def start_main_loop():
	global _thread

	# TODO: Check if running
	if _thread is not None:
		return
	with _thread_lock:
		if _thread is not None:
			return

		_thread = threading.Thread(target=_main_loop_thread, name='glib_dbus_main_loop')
		_thread.daemon = True
		_thread.start()

def unload():
	global _main_loop, _system_bus, _session_bus, _thread

	if _main_loop is not None:
		with _main_loop_lock:
			if _main_loop is not None:
				_main_loop.quit()
			_main_loop = None
	if _system_bus is not None:
		with _system_bus_lock:
			if _system_bus is not None:
				_system_bus.close()
			_system_bus = None
	if _session_bus is not None:
		with _session_bus_lock:
			if _session_bus is not None:
				_session_bus.close()
			_session_bus = None
	if _thread is not None:
		with _thread_lock:
			if _thread is not None:
				_thread.join()
			_thread = None
