#!/bin/sh
# http://talk.maemo.org/showthread.php?p=1255160

rm -fv DEBIAN/digsigsums DEBIAN/md5sums

for file in "$@"; do
	md5sum "$file" >> DEBIAN/md5sums
	echo S 15 com.nokia.maemo H 40 $(sha1sum "$file" | cut -c -40) R $(expr length "$file") $file >> DEBIAN/digsigsums
done
