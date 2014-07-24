#!/bin/sh

xrandr --output LVDS1 --mode 1366x768 --output HDMI2 --off            --output HDMI3 --off --output VGA1 --off
# Set DPI to 96 - it's not accurate, but the "correct" DPI of ~125 seems to
# scale my fonts way too high (even compared to an accurate DPI on my external
# monitors), looks horrible, causes issues for applications that don't scale
# all their UI along with the DPI (e.g. the tab bar in Firefox), and windows
# moved between monitors of differing DPIs don't get adjusted.
xrandr --dpi 96

# Need to calibrate new laptop display
dispwin -c
xprop -root -remove _ICC_PROFILE
xprop -root -remove _ICC_PROFILE_1
