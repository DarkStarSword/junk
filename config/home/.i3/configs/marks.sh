#!/bin/sh

chars='a b c d e f g h i j k l m n o p q r s t u v w x y z'

echo 'mode "mark" {'
for letter in $chars; do
	echo '  bindsym '$letter' mark '$letter'; mode "default"'
done
echo '  bindsym Escape mode "default"'
echo '}'
echo
echo 'mode "goto" {'
for letter in $chars; do
	echo '  bindsym '$letter' [con_mark="'$letter'"] focus; mode "default"'
done
echo '  bindsym Escape mode "default"'
echo '}'
echo
echo 'bindsym $mod+m mode "mark"'
echo 'bindsym $mod+apostrophe mode "goto"'
