#!/bin/sh
xrandr --output HDMI3 --mode 1920x1080 --output LVDS1 --mode 1366x768 --right-of HDMI3 --output HDMI2 --off
dispwin -I /home/ian/colorhug/results/samsung/samsung.icc
