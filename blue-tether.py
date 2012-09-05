#!/usr/bin/env python

import dbus
import subprocess
import sys
import os
import optparse

# Either pass the bluetooth address of the network access point to connect to
# with the -b flag, or store it in the config file in the form:
# bdaddr = 00:11:22:AA:BB:CC
def_config_file = '~/.blue-tether'

dhcp_clients = [
  ['/sbin/dhclient', '-v', '-d'],
  ['/sbin/udhcpc', '-f', '-i'],
]

def process_config_file(opts):
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
        raise optparse.OptionValueError('Badly formatted line in condfig file: %s' % line)
      try:
        if getattr(opts, opt) == None:
          setattr(opts, opt, val)
      except AttributeError:
        raise optparse.OptionValueError('Unknown option in config file: %s' % opt)

def get_config():
  def check_bdaddr():
    import re
    if opts.bdaddr is None:
      raise optparse.OptionValueError(
          'bdaddr must be specified with -b or in %s' % opts.config)
    if re.match('([0-9a-fA-F]{2}(:(?=.)|$)){6}$', opts.bdaddr) is None:
      raise optparse.OptionValueError('bdaddr in wrong format')

  parser = optparse.OptionParser()
  parser.add_option('-b', '--bdaddr',
    help='Bluetooth address of the network access point to connect to')
  # Coming soon:
  # parser.add_option('-r', '--reconnect', type='int', metavar='SECONDS',
  #   help='Attempt to reconnect every SECONDS if the network goes down')
  parser.add_option('-c', '--config', default=def_config_file,
    help='Process this config file (%default)')

  (opts, args) = parser.parse_args()

  if len(args):
    parser.error('Too many arguments')

  try:
    process_config_file(opts)
    check_bdaddr()
  except optparse.OptionValueError, e:
    parser.error(e)

  return opts

class dhcp_client(object):
  def __init__(self, cmd, interface):
    import atexit
    self.proc = subprocess.Popen(cmd + [interface], stdout=sys.stdout)
    atexit.register(self.cleanup)

  def cleanup(self):
    if self.proc:
      self.proc.kill()
      self.proc.wait()
      self.proc = None

  def __del__(self):
    self.cleanup()

  @staticmethod
  def exists(cmd):
    return os.path.exists(cmd[0])

def start_dhcp(interface):
  for cmd in dhcp_clients:
    if dhcp_client.exists(cmd):
      return dhcp_client(cmd, interface)
  print 'Unable to locate DHCP Client'

def main():
  opts = get_config()

  bus = dbus.SystemBus()
  bluez_proxy = bus.get_object('org.bluez', '/')
  bluez_manager = dbus.Interface(bluez_proxy, 'org.bluez.Manager')
  adapter = bluez_manager.DefaultAdapter()
  # adapter_proxy = bus.get_object('org.bluez', adapter)
  dev_proxy = bus.get_object('org.bluez', '%s/dev_%s' % (adapter, opts.bdaddr.replace(':', '_')))
  adapter_network = dbus.Interface(dev_proxy, 'org.bluez.Network')
  # adapter_introspect = dbus.Interface(dev_proxy, 'org.freedesktop.DBus.Introspectable')
  # print adapter_introspect.Introspect()
  # print adapter_network.Disconnect()
  net_interface = adapter_network.Connect('NAP') # 'GN' / 'NAP' ?
  print '%s created' % net_interface

  dhcp = start_dhcp(net_interface)

  raw_input('Press enter to close connection\n')

  del dhcp

if __name__ == '__main__':
  main()

# vim:expandtab:ts=2:sw=2
