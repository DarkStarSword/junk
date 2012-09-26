#!/usr/bin/env python

import dbus
import sys

def main():
  bdaddr = sys.argv[1]

  bus = dbus.SystemBus()
  bluez_proxy = bus.get_object('org.bluez', '/')
  bluez_manager = dbus.Interface(bluez_proxy, 'org.bluez.Manager')
  adapter = bluez_manager.DefaultAdapter()
  dev_proxy = bus.get_object('org.bluez', '%s/dev_%s' % (adapter, bdaddr.replace(':', '_')))

  adapter_device = dbus.Interface(dev_proxy, 'org.bluez.Device')
  properties = adapter_device.GetProperties()
  print '\nproperties:\n%s\n' % properties

  adapter_device.SetProperty('Trusted', True)

if __name__ == '__main__':
  main()

# vim:expandtab:ts=2:sw=2
