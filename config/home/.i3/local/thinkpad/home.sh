#!/bin/sh
xrandr --output HDMI2 --mode 1920x1080 --output LVDS1 --mode 1366x768 --right-of HDMI2 --output HDMI3 --off
dispwin -I /home/ian/colorhug/results/samsung/samsung.icc
