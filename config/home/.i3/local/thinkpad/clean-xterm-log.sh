#!/bin/sh

xterm=$(which xterm)
now=$(date +%s)
timelimit=259200 # 3 Days

if [ "$1" = "-v" ]; then
	verbose=1
fi

pr_verbose()
{
	if [ "$verbose" -ge "1" ]; then
		echo "$@"
	fi
}

for log in ~/Xterm.log.*; do
	set -- $(echo "$log"|sed 's/\./ /g')
	pid="${10}"
	if [ "$(readlink /proc/$pid/exe)" = "$xterm" ]; then
		# TODO: An edge case exists where the PID has wrapped or we have
		# rebooted and a new xterm now has the same pid as an old one.
		# I should check /proc/$pid/fd/*, but for now it doesn't matter
		# very much either way, since this situation is unlikely to
		# continue indefinitely and the log will eventually be deleted.
		pr_verbose "Skipping $log (still running)..."
		continue
	fi

	mtime=$(stat -c '%Y' "$log")
	age=$(($now - $mtime))
	if [ "$age" -gt "$timelimit" ]; then
		if [ "$verbose" -ge 1 ]; then
			rm -v "$log"
		else
			rm "$log"
		fi
	else
		pr_verbose "Skipping $log (Modified within time limit)..."
	fi
done
