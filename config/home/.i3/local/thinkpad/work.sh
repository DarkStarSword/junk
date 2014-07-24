#!/bin/sh

xrandr --output LVDS1 --off           --output HDMI2 --mode 1600x1200 --primary --output HDMI3 --mode 1600x1200 --right-of HDMI2 --output VGA1 --off
xrandr --fbmm 410x308 # Set correct DPI (this seems to need the dimensions of just one monitor?)
dispwin -d 2 -I /home/ian/colorhug/results/r_lut/thinkvision_r_lut.icc
dispwin -d 1 -I /home/ian/colorhug/results/left/thinkvision_l.icc
