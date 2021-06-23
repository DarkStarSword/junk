#!/bin/sh

mkdir portraits landscapes 2>/dev/null

for f in "$@"; do
	[ ! -f "$f" ] && continue
	# TODO: Filter out any non-image files

	# Maybe: exifautotran to normalise jpeg rotation?

	# ImageMagick to get orientation. Slow:
	#orientation=$(identify -format '%[fx:(h>w)]' "$f")

	# file + shell to get orientation. Much faster:
	test $(file -L "$f" | sed -E 's/^.*(, ([0-9]+) ?x ?([0-9]+)|, height=([0-9]+),.*, width=([0-9]+)).*$/\2\5 -gt \3\4/')
	orientation=$?

	if [ $orientation -eq 1 ]; then
		echo " portrait: $f"
		#mv "$f" portraits
		ln "$f" portraits
	else
		echo "landscape: $f"
		#mv "$f" landscapes
		ln "$f" landscapes
	fi
done
