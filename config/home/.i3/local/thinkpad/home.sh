#!/bin/sh
xrandr --output DP-2 --off --output DP-3 --off
xrandr --output DP-1 --mode 1920x1080 --output LVDS-1 --mode 1600x900 --right-of DP-1
dispwin -I /home/ian/colorhug/results/samsung/samsung.icc
