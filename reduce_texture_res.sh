#!/bin/sh

MAX_JOBS=7
TEXCONV=~/texconv.exe

find . -iname '*.dds' -print0 | while read -d $'\0' file; do
	if (file "$file" | grep -E '4096|8192' > /dev/null); then
		dir=$(dirname "$file")
		windir=$(cygpath -w "$dir")
		basename=$(basename "$file")
		echo "4k+: $file"
		mkdir -p "2k/$dir"
		# Best approach would be to discard the most detailed mip and
		# promote all the remaining mips without recompressing
		# anything, but texconv can't do that AFAICT. Next approach is
		# to resize the texture, but texconv can't do that if it has
		# mips - so we do two passes. First, resize the texture to 2k
		# and discard mip maps, then run a second pass to generate new
		# mip maps:
		(
			$TEXCONV -w 2048 -h 2048 -m 1 -sepalpha -o "2k\\$windir" "$windir\\$basename" > /dev/null
			$TEXCONV -y -sepalpha -o "2k\\$windir" "2k\\$windir\\$basename" > /dev/null
		) &
		while [ $(jobs | wc -l) -ge $MAX_JOBS ]; do
			jobs
			sleep 1
		done
	else
		echo "Not 4k: $file"
	fi
done
echo Waiting for remaining jobs to complete...
while [ $(jobs | wc -l) -ne 0 ]; do
	jobs
	sleep 1
done
