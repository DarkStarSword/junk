#!/bin/sh

xrandr --output LVDS-0 --off           --output DP-1 --mode 1600x1200 --output DP-2 --off
xrandr --output LVDS-0 --off           --output DP-1 --mode 1600x1200 --output DP-2 --mode 1600x1200 --right-of DP-1
dispwin -d 2 -I /home/ian/colorhug/results/r_lut/thinkvision_r_lut.icc
dispwin -d 1 -I /home/ian/colorhug/results/left/thinkvision_l.icc
