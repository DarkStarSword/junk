#!/bin/sh

display=$(echo -e "internal\nwork\nhome\nprojector" | dmenu -b)
script=~/.i3/local/thinkpad/"$display".sh
if [ -x "$script" ]; then
	"$script"
fi
