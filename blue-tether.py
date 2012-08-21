#!/usr/bin/env python

import dbus
import subprocess
import sys
import os

# Replace this with the bluetooth address of the Bluetooth Network Access Point
dev_bdaddr = '12_34_56_AB_CD_EF'

dhcp_clients = [
  ['/sbin/dhclient', '-v'],
  ['/sbin/udhcpc', '-i'],
]

def main():
  bus = dbus.SystemBus()
  bluez_proxy = bus.get_object('org.bluez', '/')
  bluez_manager = dbus.Interface(bluez_proxy, 'org.bluez.Manager')
  adapter = bluez_manager.DefaultAdapter()
  # adapter_proxy = bus.get_object('org.bluez', adapter)
  dev_proxy = bus.get_object('org.bluez', '%s/dev_%s' % (adapter, dev_bdaddr))
  adapter_network = dbus.Interface(dev_proxy, 'org.bluez.Network')
  # adapter_introspect = dbus.Interface(dev_proxy, 'org.freedesktop.DBus.Introspectable')
  # print adapter_introspect.Introspect()
  # print adapter_network.Disconnect()
  net_interface = adapter_network.Connect('NAP') # 'GN' / 'NAP' ?
  print '%s created' % net_interface

  dhcp = None
  for dhcp_client in dhcp_clients:
    if os.path.exists(dhcp_client[0]):
      dhcp = subprocess.Popen(dhcp_client + [net_interface], stdout=sys.stdout)
  if dhcp is None:
    print 'Unable to locate DHCP Client'

  raw_input('Press enter to close connection\n')

  dhcp.kill()
  dhcp.wait()

if __name__ == '__main__':
  main()
