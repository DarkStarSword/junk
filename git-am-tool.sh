#!/bin/sh

function is_clean()
{
	test $(git ls-files -dmo "$toplevel"|wc -l) -eq 0
}

function get_reject_files()
{
	git ls-files -o "$toplevel/*.rej"
}

function get_modified_files()
{
	git ls-files -m "$toplevel"
}

function hunk_lineno()
{
	patch="$1"
	awk '/^@@/ {print $2}' "$patch" | cut -d, -f 1 | cut -d- -f 2 | head -n 1
}

toplevel=$(git rev-parse --show-toplevel)

if [ -z "$toplevel" ]; then
	exit 1
fi

if [ ! -f "$toplevel/.git/rebase-apply/applying" ]; then
	echo No git-am in progress
	exit 1
fi

if ! is_clean; then
	echo "Working directory dirty"
	exit 1
fi

cd "$toplevel"

git apply --index --reject "$toplevel/.git/rebase-apply/patch"

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
		echo "Press enter to continue"
		read dummy
	fi
done

if [ "$applied" = "OK" ] && is_clean; then
	echo
	echo "All files resolved, you should continue by running 'git am --resolved'"
	# git am --resolved
else
	echo
	git status
	echo
	echo 'Not marking patch as resolved!'
fi
