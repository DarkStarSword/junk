#!/bin/sh

cred="[1;31;40m"
cyellow="[1;33;40m"
cgreen="[1;32;40m"

crst="[0;37;40m"

die()
{
	echo "${cred}$@${crst}"
	exit 1
}

usage_and_die()
{
	die "Usage: $0 remote_target [ --ignore-untracked ]"
}

deploy_commit="last-deployed"

remote="$1"; shift
[ -z "$remote" ] && usage_and_die

if [ "$1" = "--ignore-untracked" ]; then
	ignore_untracked=1
elif [ -n "$1" ]; then
	usage_and_die
fi

host=$(git remote -v|grep "^$remote\\s.*(push)"|perl -pe 's|^.*ssh://(.*?)/(.*) .*$|\1|')
rdir=/$(git remote -v|grep "^$remote\\s.*(push)"|perl -pe 's|^.*ssh://(.*?)/(.*) .*$|\2|')

last_commit=$(git rev-parse HEAD)
git commit -m git_remote_build_index_state
index_state=$(git rev-parse HEAD)
if [ "$ignore_untracked" = 1 ]; then
	git add -u $(git rev-parse --show-toplevel) # Otherwise it's only subdirectories
else
	git add -A $(git rev-parse --show-toplevel) # Otherwise it's only subdirectories
fi
git commit -m git_remote_build_working_tree_state
working_tree_state=$(git rev-parse HEAD)

git branch -f "$deploy_commit" "$working_tree_state"

git reset --mixed $index_state
git reset --soft $last_commit

git push --force ${remote} ${deploy_commit} || die push failed
ssh ${host} "cd ${rdir} && git checkout -f ${deploy_commit} && git reset --hard" || die remote build/reset failed

echo "------------------------------------------------------------"
echo "|          HEAD: $last_commit  |"
echo "|         Index: $index_state  |"
echo "|  Working Tree: $working_tree_state  |"
echo "------------------------------------------------------------"
