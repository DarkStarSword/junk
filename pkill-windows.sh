#!/bin/sh

if [ -z "$1" ]; then
	echo "usage: $0 task"
	exit 1
fi

pids=$(tasklist.exe | awk "/$1/"'&& NF && NF-1 { print ( $(NF-4) ) }')
for pid in $pids; do
	taskkill /PID $pid /F
done
