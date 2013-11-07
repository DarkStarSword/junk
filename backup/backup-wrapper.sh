#!/bin/bash
# Using bash for =~ operator

# Intended to be run from crontab, using something like:
# 0 12 * * 1-5 ~/bin/backup-wrapper.sh
# i.e. Run at 12PM (noon) every Monday-Friday.
#
# The encfs password should be stored in ~/.encpw - as much as I don't really
# like having the password stored like this, the script has to be able to get
# it without interactively asking somehow, and /home is encrypted (RIGHT?).
# Anyone who gains access to it likely has access to the rest of your files
# anyway.
#
# This script does NOT use passwordless SSH keys (which would be much simpler -
# everyone else should probably use that), so it will only work if there is a
# running ssh-agent with an identity loaded that can be used to log into the
# backup machine.
#
# The disadvantage of this approach is that the backup will not run if ssh-add
# has not been run since logging in. In my case that is acceptable since I
# generally run ssh-add pretty quickly and am not overly worried about the
# script not running on the odd occasion.

find_ssh_sock()
{
	for sock in /tmp/ssh-*/agent.*; do
		if env SSH_AUTH_SOCK="$sock" ssh-add -L > /dev/null; then
			echo "$sock"
		fi
	done
}

if [ -z "$SSH_AUTH_SOCK" ]; then
	export SSH_AUTH_SOCK=$(find_ssh_sock)
fi
if [ -z "$SSH_AUTH_SOCK" ]; then
	echo "Unable to find running ssh-agent or ssh-add not run, exiting"
	exit 1
fi
if ! ssh-add -L > /dev/null; then
	ssh-add -L # For error msg
	exit 1
fi

# If you only want backups to run while in a certain location, add a test here.
# The example below would only run if eth0 has an IP address like 192.168.*.*

# ip=$( ip -4 addr show eth0 | awk '/inet / {print $2}' )
# echo "$ip"
# if [[ "$ip" =~ 192\.168\.[0-9]+\.[0-9]+/16 ]]; then

	echo 'Starting backup...'
	$(dirname "$0")/backup-reverse-encfs-rdiff.sh ~/.encpw

# else
# 	echo 'Skipping backup - IP address check failed'
# fi
