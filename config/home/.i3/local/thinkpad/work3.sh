#!/bin/sh

# xrandr --output HDMI2 --mode 1600x1200 --primary --output HDMI3 --mode 1600x1200 --right-of HDMI2 --output LVDS1 --mode 1366x768 --right-of HDMI3 --output VGA1 --off
xrandr --output LVDS1 --mode 1366x768 --primary --output HDMI2 --mode 1600x1200 --right-of LVDS1 --output HDMI3 --mode 1600x1200 --right-of HDMI2 --output VGA1 --off
dispwin -d 2 -I /home/ian/colorhug/results/r_lut/thinkvision_r_lut.icc
dispwin -d 1 -I /home/ian/colorhug/results/left/thinkvision_l.icc
