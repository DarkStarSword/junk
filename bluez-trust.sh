#!/bin/sh

bdaddr=$(echo $1 | tr : _)

if [ -z "$bdaddr" ]; then
	echo Usage: $0 bl:ue:to:th:ad:dr
	exit 1
fi

adapter=$(dbus-send --system --print-reply --dest=org.bluez / org.bluez.Manager.DefaultAdapter)
adapter=$(echo $adapter|awk -F\" '{print $2}')

echo Adapter: $adapter
path=$adapter/dev_$bdaddr
echo D-Bus Path: $path

properties=$(dbus-send --system --print-reply --dest=org.bluez $path org.bluez.Device.GetProperties)

echo
echo Properties:
echo
echo $properties

dbus-send --system --print-reply --dest=org.bluez $path org.bluez.Device.SetProperty string:'Trusted' variant:boolean:true
