#!/bin/sh

is_clean()
{
	if [ "$ignore_untracked" = "1" ]; then
		test $(git ls-files -dm "$toplevel"|wc -l) -eq 0
	else
		test $(git ls-files -dmo "$toplevel"|wc -l) -eq 0
	fi
}

get_reject_files()
{
	git ls-files -o "$toplevel/*.rej"
}

get_modified_files()
{
	git ls-files -m "$toplevel"
}

hunk_lineno()
{
	patch="$1"
	awk '/^@@/ {print $2}' "$patch" | cut -d, -f 1 | cut -d- -f 2 | head -n 1
}

usage()
{
	echo "usage: $0 [ patch ]"
	exit 1
}

toplevel=$(git rev-parse --show-toplevel)

if [ -z "$toplevel" ]; then
	exit 1
fi

ignore_untracked=0
is_am=1
for arg in "$@"; do
	case "$arg" in
		'--ignore-untracked'|'-i')
			ignore_untracked=1
			;;
		*)
			if [ -n "$patch" ]; then
				usage
			fi
			patch="$arg"
			is_am=0
			if [ ! -f "$patch" ]; then
				echo "$patch not found"
				usage
			fi
			;;
	esac
done

if [ "$is_am" -eq "1" ]; then
	if [ ! -f "$toplevel/.git/rebase-apply/applying" ]; then
		echo "No git-am in progress, and no patch specified on the commandline"
		exit 1
	fi
	patch="$toplevel/.git/rebase-apply/patch"
fi

if ! is_clean; then
	echo "Working directory dirty, aborting"
	exit 1
fi

cd "$toplevel"

git apply --index --reject "$patch"

# git apply --index doesn't seem to work with --reject when only some hunks
# applied. I'm guessing (but haven't tested) that new/deleted files are OK:
for file in $(get_modified_files); do
	git add "$file"
done

for reject in $(get_reject_files); do
	file=$(dirname "$reject")/$(basename "$reject" ".rej")
	lineno=$(hunk_lineno "$reject")
	orig_sha1=$(sha1sum "$file")
	vim -O "+$lineno" "$file" "$reject"
	new_sha1=$(sha1sum "$file")
	if [ "$new_sha1" != "$orig_sha1" ]; then
		git add "$file"
		rm -v "$reject"
		if [ -z "$applied" ]; then
			applied=OK
		fi
	else
		applied=FAIL
		echo "WARNING: File unchanged, not cleaning up $reject"
		# FIXME: Ask to continue, abort leaving .rej, abort cleaning up, etc.
		echo "Press enter to continue"
		read dummy
	fi
done

if [ "$applied" = "OK" ] && is_clean; then
	echo
	if [ "$is_am" -eq "1" ]; then
		echo "All files resolved, you should continue by running 'git am --resolved'"
	else
		echo "All files resolved, you should now commit the result"
	fi
	# git am --resolved
else
	echo
	git status
	echo
	echo 'Not marking patch as resolved!'
fi
