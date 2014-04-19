#!/usr/bin/env python

import dbus
import subprocess
import sys
import os
import optparse

from dbus.mainloop.glib import DBusGMainLoop
import glib, gobject

def_config_file = '~/.bluenetap'

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
  parser = optparse.OptionParser()
  parser.add_option('-a', '--adapter',
    help='Which bluetooth adapter to use if more than one are available')
  parser.add_option('-c', '--config', default=def_config_file,
    help='Process this config file (%default)')

  (opts, args) = parser.parse_args()

  if len(args):
    parser.error('Too many arguments')

  process_config_file(opts, parser)

  return opts

class udhcpd(object):
  cmd = ['/usr/sbin/udhcpd', '-f']
  proc = None # In case of race between __init__ and __del__
  def __init__(self):
    import atexit
    print 'Starting DHCP server...'
    self.config = self.gen_config()
    self.proc = subprocess.Popen(self.cmd + [self.config], stdout=sys.stdout, stderr=sys.stderr)
    atexit.register(self.cleanup)

  def gen_config(self):
    interface = 'bnep0' # FIXME: How am I supposed to be notified of this when the interface is connected?
    # FIXME: For that matter, I need to know that to configure the interface anyway... I guess I could always poll...

  def cleanup(self):
    if self.proc:
      print 'Stopping DHCP server...'
      self.proc.kill()
      self.proc.wait()
      self.proc = None

  def __del__(self):
    print 'DHCP DEL'
    self.cleanup()

  @classmethod
  def exists(cls):
    return os.path.exists(cls.cmd[0])

dhcp_servers = [
  udhcpd,
]

def start_dhcp():
  for server in dhcp_servers:
    if server.exists():
      return server()
  print 'Unable to locate DHCP Server'


class BluezNAP(object):
  def __init__(self, bus, adapter, main_loop):
    self.bus = bus
    self.main_loop = main_loop

    self.dhcp = None

    self.dev_network = dbus.Interface(adapter, 'org.bluez.NetworkServer')

    self.start()

  def start(self):
    print 'Starting NAP...'
    try:
      self.dev_network.Register('nap', '')
      print 'NAP started'
      # self.dhcp = start_dhcp()
      return 0
    except dbus.exceptions.DBusException, e:
      print 'Error Starting NAP: %s' % e
      raise

  def __del__(self):
    self.dev_network.Unregister('nap')
    if self.dhcp is not None:
      self.dhcp.cleanup()
      self.dhcp = None

def main():
  opts = get_config()

  #dbus.glib.threads_init()
  #glib.theads_init()

  bus_loop = DBusGMainLoop(set_as_default = True)
  main_loop = glib.MainLoop()

  bus = dbus.SystemBus()
  bluez_proxy = bus.get_object('org.bluez', '/')
  bluez_manager = dbus.Interface(bluez_proxy, 'org.bluez.Manager')
  if opts.adapter is not None:
    adapter = bluez_manager.FindAdapter(opts.adapter)
  else:
    adapter = bluez_manager.DefaultAdapter()

  adapter = bus.get_object('org.bluez', adapter)

  def input_callback(*args):
    # print 'INPUT: %s' % repr(args)
    main_loop.quit()
    return True # What return value signifies what?

  glib.io_add_watch(sys.stdin, glib.IO_IN, input_callback)
  try:
    bluez_net_monitor = BluezNAP(bus, adapter, main_loop)
  except dbus.exceptions.DBusException, e:
    return 1

  print 'Press enter to close connection'
  main_loop.run()

if __name__ == '__main__':
  main()

# vim:expandtab:ts=2:sw=2
