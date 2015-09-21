#!/bin/sh

display=$(/bin/echo -e "internal\nhome\nwork-tb\nwork\nwork3\nprojector\nprojector-640x480" | dmenu -b)
script=~/.i3/local/thinkpad/"$display".sh
if [ -x "$script" ]; then
	"$script"
fi

feh --bg-fill ~/desktop.jpg
# feh --bg-center ~/desktop.jpg
