#!/bin/sh

ifconfig bnep0 192.168.2.14 up
udhcpd -f bluenetap-udhcpd.conf
