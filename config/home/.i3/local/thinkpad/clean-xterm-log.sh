#!/bin/sh

xterm=$(which xterm)
now=$(date +%s)
timelimit=259200 # 3 Days

for log in ~/Xterm.log.*; do
	set -- $(echo "$log"|sed 's/\./ /g')
	pid="${10}"
	if [ "$(readlink /proc/$pid/exe)" != "$xterm" ]; then
		# TODO: An edge case exists where the PID has wrapped or we have
		# rebooted and a new xterm now has the same pid as an old one.
		# I should check /proc/$pid/fd/*, but for now it doesn't matter
		# very much either way, since this situation is unlikely to
		# continue indefinitely and the log will eventually be deleted.
		continue
	fi

	mtime=$(stat -c '%Y' "$log")
	age=$(($now - $mtime))
	if [ "$age" -gt "$timelimit" ]; then
		rm "$log"
	fi
done
