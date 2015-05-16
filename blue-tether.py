#!/usr/bin/env python

import dbus
import subprocess
import sys
import os
import optparse
import re

from dbus.mainloop.glib import DBusGMainLoop
import glib, gobject

# Either pass the bluetooth address of the network access point to connect to
# with the -b flag, or store it in the config file in the form:
# bdaddr = 00:11:22:AA:BB:CC
def_config_file = '~/.blue-tether'

dhcp_clients = [
  ['/sbin/dhclient', '-v', '-d'],
  ['/sbin/udhcpc', '-f', '-i'],
]

# FUCKING BLUEZ DEVS!
# In Bluez 4, this is 'org.bluez.Network'
# In Bluez 5, this is 'org.bluez.Network1'
# And the DBUS API means we won't find out until later if we got it wrong!
# Currently relying on another Bluez 5 breakage to switch this string...
# TODO: introspect which is in use instead
BLUEZ_NETWORK_IFACE = 'org.bluez.Network'

def process_config_file(opts, parser):
  opts.config = os.path.expanduser(opts.config)
  if not os.path.isfile(opts.config):
    return
  with open(opts.config, 'r') as f:
    for line in f:
      line = line.split('#', 1)[0].strip()
      if line == '':
        continue
      try:
        (opt, val) = map(str.strip, line.split('=', 1))
      except ValueError:
        parser.error('Badly formatted line in condfig file: %s' % line)
      try:
        if getattr(opts, opt) == None:
          val = parser.get_option('--%s'%opt).convert_value(opt, val)
          setattr(opts, opt, val)
      except AttributeError:
        parser.error('Unknown option in config file: %s' % opt)

def get_config():
  def check_bdaddr():
    import re
    if opts.bdaddr is None:
      parser.error( 'bdaddr must be specified with -b or in %s' % opts.config)
    if re.match('([0-9a-fA-F]{2}(:(?=.)|$)){6}$', opts.bdaddr) is None:
      parser.error('bdaddr in wrong format')

  parser = optparse.OptionParser()
  parser.add_option('-a', '--adapter',
    help='Which bluetooth adapter to use if more than one are available')
  parser.add_option('-b', '--bdaddr',
    help='Bluetooth address of the network access point to connect to')
  parser.add_option('-r', '--reconnect', type='int', metavar='SECONDS',
    help='Attempt to reconnect every SECONDS if the network goes down')
  parser.add_option('-c', '--config', default=def_config_file,
    help='Process this config file (%default)')

  (opts, args) = parser.parse_args()

  if len(args):
    parser.error('Too many arguments')

  process_config_file(opts, parser)
  check_bdaddr()

  return opts

class dhcp_client(object):
  proc = None # In case of race between __init__ and __del__
  def __init__(self, cmd, interface):
    import atexit
    print 'Starting DHCP client...'
    self.proc = subprocess.Popen(cmd + [interface], stdout=sys.stdout)
    atexit.register(self.cleanup)

  def cleanup(self):
    if self.proc:
      print 'Stopping DHCP client...'
      self.proc.kill()
      self.proc.wait()
      self.proc = None

  def __del__(self):
    print 'DHCP DEL'
    self.cleanup()

  @staticmethod
  def exists(cmd):
    return os.path.exists(cmd[0])

def start_dhcp(interface):
  for cmd in dhcp_clients:
    if dhcp_client.exists(cmd):
      return dhcp_client(cmd, interface)
  print 'Unable to locate DHCP Client'


class BluezNetMonitor(object):
  def __init__(self, bus, bd_path, main_loop, reconnect = None):
    self.bus = bus
    self.bd_path = bd_path
    self.main_loop = main_loop
    self.reconnect = reconnect

    self.props = {
        'Connected': 0,
        'Interface': '',
        'UUID': '',
      }
    self.Connected = property(lambda: self.props['Connected'], lambda x: self.props.__setitem__('Connected', x))
    self.Interface = property(lambda: self.props['Interface'], lambda x: self.props.__setitem__('Interface', x))

    self.dhcp = None
    self.is_up = False

    self.dev_proxy = self.bus.get_object('org.bluez', self.bd_path)
    self.dev_network = dbus.Interface(self.dev_proxy, BLUEZ_NETWORK_IFACE)

    # More Bluez 4/5 differences:
    bus.add_signal_receiver(self.property_changed_callback, 'PropertyChanged',
        BLUEZ_NETWORK_IFACE, None, bd_path)
    bus.add_signal_receiver(self.properties_changed_callback_bluez5, 'PropertiesChanged',
        'org.freedesktop.DBus.Properties', None, bd_path)

    self.connect()

  def property_changed_callback(self, prop, val):
    print 'Property Changed: %s: %s' % (prop, val)
    if prop == 'Interface' and self.is_up and val != self.Interface:
      self.down()
    self.props[prop] = val
    if prop == 'Connected':
      val and self.up()
      val or self.down()

  def properties_changed_callback_bluez5(self, interface, objects, signature):
    print 'Properties Changed (Bluez 5): %s: %s (%s)' % (interface, objects, signature)
    if interface != BLUEZ_NETWORK_IFACE:
      return
    if 'Interface' in objects:
      if self.is_up and objects['Interface'] != self.Interface:
        self.down()
      self.props['Interface'] = objects['Interface']
    if 'Connected' in objects:
      self.props['Connected'] = objects['Connected']
      objects['Connected'] and self.up()
      objects['Connected'] or self.down()

  def up(self):
    if self.is_up:
      print 'ALREADY UP'
      return
    print 'UP'
    self.is_up = True
    assert(self.dhcp is None)
    self.dhcp = start_dhcp(self.Interface)

  def down(self):
    if self.is_up == False:
      print 'ALREADY DOWN'
      return
    print 'DOWN'
    self.is_up = False
    if self.dhcp is not None:
      self.dhcp.cleanup()
      self.dhcp = None
    self.no_connection()

  def no_connection(self):
    if self.reconnect is None:
      print 'Auto reconnect disabled, quitting...'
      self.main_loop.quit()
    else:
      print 'Will retry every %d seconds' % self.reconnect
      glib.timeout_add(self.reconnect * 1000, self._connect)

  def _connect(self):
    print 'Connecting...'
    try:
      self.Interface = self.dev_network.Connect('NAP') # 'GN' / 'NAP' ?
      print '%s created' % self.Interface
      return 0
    except dbus.exceptions.DBusException as e:
      print 'Error Connecting: %s' % e
      if self.reconnect is None:
        raise
      return 1

  def connect(self):
    ret = self._connect()
    if ret: self.no_connection()
    return ret

  def disconnect(self):
    print 'Disconnecting...'
    self.dev_network.Disconnect()

class AdapterNotFound(Exception): pass

def fucking_bluez_devs_hate_backwards_compatibility_what_bloody_arseholes(bus, adapter=None):
  global BLUEZ_NETWORK_IFACE
  bluez_proxy = bus.get_object('org.bluez', '/')
  try: # the old method that worked in Bluez 4 (of course, the bluez 3 method was broken years ago):
    bluez_manager = dbus.Interface(bluez_proxy, 'org.bluez.Manager')
    if adapter is None:
      return bluez_manager.DefaultAdapter()
    return bluez_manager.FindAdapter(adapter)
  except dbus.exceptions.DBusException:
    print('Bluez developers SUCK!')
    BLUEZ_NETWORK_IFACE = 'org.bluez.Network1'
    # There's probably a more direct way to get this info built into the Python
    # DBUS API...
    manager = dbus.Interface(bluez_proxy, 'org.freedesktop.DBus.ObjectManager')
    objects = manager.GetManagedObjects()
    pattern = re.compile(r'/org/bluez/[^/]+$')
    adapters = filter(lambda x: pattern.match(x), objects.keys())
    if adapter is None:
      return sorted(adapters)[0]
    for path in adapters:
      proxy = bus.get_object('org.bluez', path)
      # Probably a more direct way to do this too...
      properties = dbus.Interface(proxy, dbus.PROPERTIES_IFACE)
      address = properties.Get('org.bluez.Adapter1', 'Address')
      if address.lower() == adapter.lower():
        return path
    raise AdapterNotFound(adapter)

def main():
  opts = get_config()

  #dbus.glib.threads_init()
  #glib.theads_init()

  bus_loop = DBusGMainLoop(set_as_default = True)
  main_loop = glib.MainLoop()

  bus = dbus.SystemBus()
  # FIXME: BROKEN IN BLUEZ 5!!!!
  adapter = fucking_bluez_devs_hate_backwards_compatibility_what_bloody_arseholes(bus, opts.adapter)

  bd_path = '%s/dev_%s' % (adapter, opts.bdaddr.upper().replace(':', '_'))

  def input_callback(*args):
    # print 'INPUT: %s' % repr(args)
    main_loop.quit()
    return True # What return value signifies what?

  glib.io_add_watch(sys.stdin, glib.IO_IN, input_callback)
  try:
    bluez_net_monitor = BluezNetMonitor(bus, bd_path, main_loop, opts.reconnect)
  except dbus.exceptions.DBusException as e:
    return 1

  print 'Press enter to close connection'
  main_loop.run()

  # Bluez 5 now seem to require manual disconnection... probably for the best,
  # but an incompatible change none the less:
  bluez_net_monitor.disconnect()

if __name__ == '__main__':
  main()

# vim:expandtab:ts=2:sw=2
