#!/bin/sh

for file in "$@"; do

	echo -n "$file - "
	unzip -v "$file" | head -n -2 | tail -n +4 | awk '{print $7 " " $8}' | sort | sha1sum

done
