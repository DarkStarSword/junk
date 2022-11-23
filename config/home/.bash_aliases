#!/bin/bash

# If not running interactively, don't do anything
[[ "$-" != *i* ]] && return

# https://stackoverflow.com/questions/3466166/how-to-check-if-running-in-cygwin-mac-or-linu://stackoverflow.com/questions/3466166/how-to-check-if-running-in-cygwin-mac-or-linux
case "$(uname -s)" in
    Linux*)     case "$(uname -r)" in
					*Microsoft*)	machine=WSL1;;
					*microsoft*)	machine=WSL2;;
					*)				machine=Linux;;
				esac;;
    Darwin*)    machine=Mac;;
    CYGWIN*)    machine=Cygwin;;
    MINGW*)     machine=MinGw;;
    *)          machine="UNKNOWN:${unameOut}"
esac

HISTCONTROL=ignoreboth
shopt -s histappend
HISTSIZE=1000
HISTFILESIZE=2000
shopt -s checkwinsize

if [ -d "$HOME/bin" ]; then
	export PATH="$HOME/bin:$PATH"
fi

stoopid_mac_rgrep()
{
	# Workaround recursive grep on mac trying to search stdin instead of the
	# filesystem when no directory specified
	if [ "$machine" != "Mac" ]; then
		return
	fi
	n=0
	while (( "$#" )); do
		case "$1" in
			-*) ;;
			 *) n=$(($n+1)) ;;
		esac
		shift 1
	done
	if [ $n -ge 2 ]; then
		# User already specified the path
		return
	fi
	echo .
}

if [ "$machine" == "Mac" ]; then
	alias ls='ls -F -G'
	rgrep()
	{
		grep -r --color=auto "$@" $(stoopid_mac_rgrep "$@")
	}
else
	alias ls='ls -F --color=auto'
	alias 'rgrep=grep -r --color=auto'
fi

set -o vi
bind -m vi-insert "\C-l":clear-screen
alias 'rg=rgrep'
alias 'rgi=rgrep -i'
alias cdr='cd "$(readlink -f "$PWD")"'
alias td='tmux detach-client -a'
alias ta='tmux attach'
export EDITOR=vim
alias convert='gm convert'
alias -- '-=cd -'

# poor mans substitute for fish's up one level shortcuts. Ideally would alias
# ../.. = cd ../.., etc, but can't have a / in the alias, so just .... = cd ../..:
for x in $(seq 10); do
   lhs=${lhs}..
   rhs=${rhs}../
   alias "${lhs}=cd ${rhs}"
done

if [ ! -S "$SSH_AUTH_SOCK" ]; then
	# 10 Minute default as compromise between security + convinience on systems
	# without a definite policy. Keys still won't be added at all unless
	# AddKeysToAgent is enabled in ~/.ssh/config or ssh-add is manually run.
	kill_ssh_agent()
	{
		ssh-agent -k
	}
	trap kill_ssh_agent EXIT
	eval $(ssh-agent -s -t 10m)
	# If we are running inside tmux and the ssh agent was unreachable, set it
	# to the new one we just spawned. This will still be subject to being
	# killed when this shell terminates rather than tmux as a whole, but I'd
	# prefer that over leaving a detached ssh-agent running.
	if [ -n "$TMUX" ]; then
		tmux set-environment SSH_AGENT_PID "$SSH_AGENT_PID"
		tmux set-environment SSH_AUTH_SOCK "$SSH_AUTH_SOCK"
	fi
fi

lst()
{
	 ls -lht "$@"|head|tac
}

gg()
{
	if test -t 1; then
		git grep "$@" 2>/dev/null || grep -r --color=always "$@" $(stoopid_mac_rgrep "$@") | less -R -F -X
	else
		git grep "$@" 2>/dev/null || grep -r "$@" $(stoopid_mac_rgrep "$@") | less -F -X
	fi
}

ggh()
{
	if test -t 1; then
      find . -iname '*.h' -print0 | xargs -0 grep -r --color=always "$@" $(stoopid_mac_rgrep "$@") | less -R -F -X
	else
      find . -iname '*.h' -print0 | xargs -0 grep -r "$@" $(stoopid_mac_rgrep "$@") | less -F -X
	fi
}

if [ "$machine" = "WSL1" -o "$machine" = "WSL2" ]; then
	winenv()
	{
		# See also: WSLENV to translate paths in environment variables passed to/from WSL
		#           https://devblogs.microsoft.com/commandline/share-environment-vars-between-wsl-and-windows/
		cmd.exe /c echo "%$1%" 2>/dev/null | tr -d '\r'
	}

	if [ "$machine" = "WSL1" ]; then
		# Attempt to get location of WSL root in Windows. Not positive what the
		# correct way to get this is.
		export WSL_ROOTFS_WIN="$(wslpath -w "$(ls -d "$(wslpath "$(winenv LOCALAPPDATA)")"/Packages/*${WSL_DISTRO_NAME}*/LocalState/rootfs)")"

		cygpath()
		{
			# wslpath mostly takes the place of cygpath, but doesn't expand the wsl
			# root path when operated on a folder outside of a /mnt/ point. That is
			# okay - explorer knows how to open the wsl$ URLs, but this should give
			# us a way to easily find the real location:
			wslpath "$@" | sed 's|\\\\wsl\$\\'"${WSL_DISTRO_NAME}"'\\|'"${WSL_ROOTFS_WIN//\\/\\\\}"'|'
		}
	else
		# WSL2 uses a loopback ext4 image, so WSL paths are not directly
		# accessible to Windows as they were before, and wslpath now returns
		# "\\wsl.localhost\" in WSL2 instead of "wsl$" as it did in WSL1, so
		# may work directly with applications that can handle windows network
		# paths.
		alias cygpath=wslpath
	fi

	# Substituted (virtual) drive letters aren't mounted automatically in WSL.
	# Parse the subst.exe output and symlink them as appropriate. Handles case
	# where the target has changed.
	# XXX: Untested on WSL2
	while read -r line; do
		wintarget="$(echo "$line" | sed -E 's/^.* => (.*)\r$/\1/;')"
		lintarget="$(cygpath "$wintarget")"
		drive="$(echo "$line" | sed -E 's/([A-Z]):.*$/\L\1/')"
		linmount="/mnt/$drive"
		if [ \( ! -e "$linmount" \) -o \( -h "$linmount" -a "$(readlink "$linmount")" != "$lintarget" \) ]; then
			echo "Mounting substituted drive $drive: ($wintarget) at $linmount..."
			sudo ln -snf "$lintarget" "$linmount"
		fi
	done < <(subst.exe)
fi

if [ "$machine" = "Cygwin" ]; then
	#alias sudo='cygstart --action=runas'
	sudo()
	{
		if [ ! -e ~/.cygwin-sudo ]; then
			echo Installing cygwin-sudo...
			git clone git://github.com/Chronial/cygwin-sudo ~/.cygwin-sudo
		fi
		~/.cygwin-sudo/cygwin-sudo.py "$@"
	}
fi

if [ "$machine" = "Cygwin" -o "$machine" = "WSL1" -o "$machine" = "WSL2" ]; then
	cdw()
	{
		path="$(cygpath "$@")"
		if [ -f "$path" ]; then
			path="$(dirname "$path")"
		fi
		cd "$path"
	}

	alias pwdw='cygpath -wa .'
	alias cu='cygpath -ua'
	alias cw='cygpath -wa'

	vimw()
	{
		cdw "$@"
		vim "$(cygpath "$@")"
	}

	# mathomatic doesn't work so well in cygwin... this alias at least sets it to
	# use ANSI colour, but readline is broken. Works better in conemu.
	# Windows/cygwin gnuplot must be installed separately for plot command to work:
	#alias 'mathomatic=~/winam2/mathomatic -a'
	mathomatic()
	{
		CONEMU="$(cygpath 'C:\Program Files\ConEmu\ConEmu64.exe')"
		MATHOMATIC=~/winam2/mathomatic.exe
		if [ -x "$MATHOMATIC" ]; then
			if [ -x "$CONEMU" ]; then
				"$CONEMU" "$(cygpath -w "$MATHOMATIC")"
			elif [ -x "$MATHOMATIC" ]; then
				"$MATHOMATIC"
			fi
		else
			"$(type -f mathomatic)"
		fi
	}

	# Replacements for pgrep/pkill that work with windows apps
	wpgrep()
	{
		if [ -z "$1" ]; then
			echo "usage: wpgrep pattern"
			return
		fi

		tasklist.exe /FO CSV | awk -F'^"|","' '$2 ~ /'"$1"'/ {print $3}'
	}
	wpkill()
	{
		if [ -z "$1" ]; then
			echo "usage: wpkill pid"
			return
		fi

		for pid in $(wpgrep "$@"); do
			taskkill.exe /PID $pid /F
		done
	}
	if ! command -v pgrep >/dev/null; then
		pgrep()
		{
			echo pgrep not found. Running wpgrep instead. Below PIDs will be Windows PIDs
			wpgrep "$@"
		}
	fi
	if ! command -v pkill >/dev/null; then
		# PIDs not shown to user, so doesn't matter that they are windows PIDs
		alias pkill=wpkill
	fi

	p4c()
	{
		# Compensate for the p4 client's lack of a sensibly easy way to switch
		# to the appropriate workspace for the current directory

		# 1. Get list of possible workspaces matching this directory. p4
		# command line can filter to the current user, then we filter to any
		# with a workspace root that is [a parent to] the current directory.
		# FIXME: Handle spaces in workspace name or directory
		local clients="$(p4.exe clients --me | awk -v PWDW="$(pwdw|sed 's/\\/\\\\/g')\\\\" \
		'{
			if (tolower($5."\\") == tolower(substr(PWDW, 0, length($5)+1))) {
				print $2
			}
		}')"

		# 2. We may still have found multiple matching workspaces if the user
		# works/builds on multiple machines. Iterate over each looking for one
		# with a hostname matching the current machine. If for some reason
		# there are still multiple matches we just go with the first.
		local client
		for client in $clients; do
			local p4host="$(p4.exe client -o "$client" | awk '/^Host:/ {gsub("\r","",$2); print $2}')"
			if [ "$p4host" = "$HOSTNAME" ]; then
				p4.exe set p4client="$client"
				p4.exe info | grep '^Client name:'
				return
			fi
		done
		echo "Cannot find p4 workspace for current directory"
	}

	p4a()
	{
		p4.exe add $(cw "$@")
	}

	p4e()
	{
		p4.exe edit $(cw "$@")
	}
fi

# Change color if this is a remote shell to help user notice if they are typing
# into wrong shell. Except, if the shell is under tmux we leave the original
# colour, since my .tmux.conf already sets the status bar colour for remote
# sessions, and in this case we want the shell prompt in each pane to indicate
# whether we are local *relative to the tmux session*, or remote from it.
PS1_COLOR=32
if [ -n "$SSH_CONNECTION" -a -z "$TMUX" ]; then
   PS1_COLOR=36
fi

if command -v git >/dev/null; then
	# Mac users who have uninstalled Xcode may have a broken git binary left in
	# place, which pops up an annoying as fuck dialog when it is run, and if we
	# enable git-prompt that means every damn time the shell prompt displays.
	# Make sure this is not Mac, or Xcode is installed to continue:
	if [ "$machine" != "Mac" -o -x "/Applications/Xcode.app" ]; then
		if [ ! -e ~/.git-prompt.sh ]; then
			echo ~/git-prompt.sh is missing, installing...
			curl -L https://raw.github.com/git/git/master/contrib/completion/git-prompt.sh > ~/.git-prompt.sh
		fi
		if [ -e ~/.git-prompt.sh ]; then
			. ~/.git-prompt.sh
			#PS1='[\u@\h \W$(__git_ps1 " (%s)")]\$ ' # git-prompt.sh example
			#PS1='\[\e]0;\w\a\]\n\[\e[32m\]\u@\h \[\e[33m\]\w\[\e[0m\]\n\$ ' # cygwin default
			#PS1='\[\e]0;\w\a\]\n\[\e[32m\]\u@\h \[\e[33m\]\w\[\e[0m\]\n$(__git_ps1 "(%s)")\$ '

			# Alernate method with colour support:
			GIT_PS1_SHOWSTASHSTATE=1
			GIT_PS1_SHOWCOLORHINTS=1
			GIT_PS1_SHOWUPSTREAM="auto"
			# Slow option - GIT_PS1_SHOWDIRTYSTATE=1
			# Slow option - GIT_PS1_SHOWUNTRACKEDFILES=1
			#PROMPT_COMMAND='__git_ps1 "\u@\h:\w" "\\\$ "' # git-prompt.sh example
			PROMPT_COMMAND='__git_ps1 "\[\e]0;\w\a\]\n\[\e['$PS1_COLOR'm\]\u@\h \[\e[33m\]\w\[\e[0m\]" "\n$ "'
		fi
	fi
fi
