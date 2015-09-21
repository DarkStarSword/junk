#!/bin/sh

xrandr --output VGA1 --mode 1600x1200 --primary --output LVDS1 --mode 1366x768 --below VGA1
xcalib -c
