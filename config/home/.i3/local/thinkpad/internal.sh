#!/bin/sh

xrandr --output LVDS1 --off           --output HDMI2 --mode 1600x1200 --output HDMI3 --off --output VGA1 --off
xrandr --output LVDS1 --mode 1366x768 --output HDMI2 --off            --output HDMI3 --off --output VGA1 --off

# Need to calibrate new laptop display
dispwin -c
xprop -root -remove _ICC_PROFILE
xprop -root -remove _ICC_PROFILE_1
