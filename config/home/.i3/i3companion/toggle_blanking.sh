#!/bin/sh

if xset q | grep 'DPMS is Enabled'; then
	xset s off
	xset -dpms
	notify-send -t 1000 'Screen Blanking DISABLED'
else
	xset s on
	xset +dpms
	notify-send -t 1000 'Screen Blanking Enabled'
fi
