#!/bin/sh

if [ ! -d .git ]; then
	echo Run me in the root of a git tree
	exit 1
fi

while true; do
	# [0-9]+ here is to ignore some weird files that vim seems to create
	# and delete before doing it's actual save/backup dance. Now that I
	# explicitly wait for the filesystem to settle I could probably remove
	# it pretty safely.
	inotifywait -e close_write -q -r --exclude '.*\.swp?x?|[0-9]+|\.git' .

	while true; do

		echo -n Waiting for filesystem to settle...
		while inotifywait -t 1 -q -q -r .; [ $? -ne 2 ]; do
			echo -n .
			sleep 0.1
		done
		echo

		if ls .git/rebase-* 2>/dev/null; then
			echo Waiting for in progress git rebase to finish...
			inotifywait -e delete -q -r .git/rebase-*
			continue
		fi

		if ls .git/*.lock 2>/dev/null; then
			echo Waiting for lock to clear...
			inotifywait -e delete -q -r .git/*.lock
			continue
		fi

		# TODO: Look for other signs that git is in the middle of something...

	break; done

	git-push-wd.sh "$@"
	echo
done
