#!/bin/sh

case "$1" in
suspend|hibernate)
	chvt 1
	;;
resume|thaw)
	chvt 7
	;;
esac
exit 0
