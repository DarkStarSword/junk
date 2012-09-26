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

deploy_commit="last-deployed"

remote="$1"; shift
[ -z "$remote" ] && die Usage: remote_target

host=$(git remote -v|grep "^$remote\\s.*(push)"|perl -pe 's|^.*ssh://(.*?)/(.*) .*$|\1|')
rdir=/$(git remote -v|grep "^$remote\\s.*(push)"|perl -pe 's|^.*ssh://(.*?)/(.*) .*$|\2|')

last_commit=$(git rev-parse HEAD)
git commit -m git_remote_build_index_state
index_state=$(git rev-parse HEAD)
git add -A $(git rev-parse --show-toplevel) # Otherwise it's only subdirectories
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
