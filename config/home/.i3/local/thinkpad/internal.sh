#!/bin/sh

xrandr --output LVDS-0 --off           --output DP-1 --mode 1600x1200 --output DP-2 --off --output VGA-0 --off
xrandr --output LVDS-0 --mode 1600x900 --output DP-1 --off            --output DP-2 --off --output VGA-0 --off
feh --bg-fill ~/desktop.jpg
dispwin -I /home/ian/colorhug/results/w510/w510.icc
