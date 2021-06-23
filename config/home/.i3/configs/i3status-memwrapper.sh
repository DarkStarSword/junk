#!/bin/sh

update_mem_available() {
	mem_available=$(awk '/MemAvailable/ {print $2}' /proc/meminfo)
	mem_available_human=$(numfmt --to=iec-i --suffix=B --format="%.1f" --from-unit=1Ki $mem_available)
	colour=
	if [ ${mem_available} -lt 204800 ]; then
		colour=",\"color\":\"#FFFF00\""
		if [ ${mem_available} -lt 102400 ]; then
			colour=",\"color\":\"#FF0000\""
		fi
	fi
	output="[{\"full_text\":\"M ${mem_available_human}\"${colour}}"
}

i3status "$@" | (
	read line && echo "$line" # Version
	read line && echo "$line" # [
	read line
	update_mem_available
	echo "${output},${line#\[}"
	while :; do
		read line
		update_mem_available
		echo ",${output},${line#,\[}" || exit 1
	done
)
