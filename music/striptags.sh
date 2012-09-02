#!/bin/sh

oktags="COMM TALB TBPM TCMP TCOM TCON TDRC TIT2 TPE1 TPOS TRCK MCDI TFLT TLEN TDTG"

indexfile=`mktemp`

#Determine tags present:
find . -iname "*.mp3" -exec eyeD3 -v {} \; > $indexfile
tagspresent=`sort -u $indexfile | awk -F\): '/^<.*$/ {print $1}' | uniq | awk -F\)\> '{print $1}' | awk -F\( '{print $(NF)}' | awk 'BEGIN {ORS=" "} {print $0}'`

rm $indexfile

#Determine tags to strip:
tostrip=`echo -n $tagspresent $oktags $oktags | awk 'BEGIN {RS=" "; ORS="\n"} {print $0}' | sort | uniq -u | awk 'BEGIN {ORS=" "} {print $0}'`

#Confirm action:
echo
echo The following tags have been found in the mp3s:
echo $tagspresent
echo These tags are to be stripped:
echo $tostrip
echo The tags will also be converted to ID3 v2.4 where possible
echo
echo -n Press enter to confirm, or Ctrl+C to cancel...
read dummy

#Strip 'em
stripstring=`echo $tostrip | awk 'BEGIN {FS="\n"; RS=" "} {print "--set-text-frame=" $1 ": "}'`
find . -iname "*.mp3" -exec eyeD3 --to-v2.4 $stripstring {} \; | tee -a striptags.log
