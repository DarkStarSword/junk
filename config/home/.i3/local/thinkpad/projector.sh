#!/bin/sh

xrandr --output LVDS-0 --mode 1600x900 --primary --output DP-1 --off --output DP-2 --off --output VGA-0 --off
xrandr --output LVDS-0 --mode 1600x900 --primary --output DP-1 --off --output DP-2 --off --output VGA-0 --mode 1024x768 --right-of LVDS-0
feh --bg-fill ~/desktop.jpg
xcalib -c
