#!/bin/bash

# If not running interactively, don't do anything
[[ "$-" != *i* ]] && return

# https://stackoverflow.com/questions/3466166/how-to-check-if-running-in-cygwin-mac-or-linu://stackoverflow.com/questions/3466166/how-to-check-if-running-in-cygwin-mac-or-linux
case "$(uname -s)" in
    Linux*)     case "$(uname -v)" in
					*Microsoft*)	machine=WSL;;
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
alias '..=cd ..' # poor mans single level only substitute for fish's up one level shortcut
alias cdr='cd "$(readlink -f "$PWD")"'
alias td='tmux detach-client -a'
export EDITOR=vim
alias convert='gm convert'

if [ ! -S "$SSH_AUTH_SOCK" ]; then
	# 10 Minute default as compromise between security + convinience on systems
	# without a definite policy. Keys still won't be added at all unless
	# AddKeysToAgent is enabled in ~/.ssh/config or ssh-add is manually run.
	kill_ssh_agent()
	{
		kill "$SSH_AGENT_PID"
	}
	trap kill_ssh_agent EXIT
	eval $(ssh-agent -s -t 10m)
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

if [ "$machine" = "WSL" ]; then
	winenv()
	{
		# See also: WSLENV to translate paths in environment variables passed to/from WSL
		#           https://devblogs.microsoft.com/commandline/share-environment-vars-between-wsl-and-windows/
		cmd.exe /c echo "%$1%" 2>/dev/null | tr -d '\r'
	}

	# Attempt to get location of WSL root in Windows. Not positive what the
	# correct way to get this is.
	export WSL_ROOTFS_WIN="$(wslpath -w "$(ls -d $(wslpath "$(winenv LOCALAPPDATA)")/Packages/*${WSL_DISTRO_NAME}*/LocalState/rootfs)")"

	cygpath()
	{
		# wslpath mostly takes the place of cygpath, but doesn't expand the wsl
		# root path when operated on a folder outside of a /mnt/ point. That is
		# okay - explorer knows how to open the wsl$ URLs, but this should give
		# us a way to easily find the real location:
		wslpath "$@" | sed 's|\\\\wsl\$\\'"${WSL_DISTRO_NAME}"'\\|'"${WSL_ROOTFS_WIN//\\/\\\\}"'|'
	}

	# Substituted (virtual) drive letters aren't mounted automatically in WSL.
	# Parse the subst.exe output and symlink them as appropriate. Handles case
	# where the target has changed.
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

if [ "$machine" = "Cygwin" -o "$machine" = "WSL" ]; then
	cdw()
	{
		path="$(cygpath "$@")"
		if [ -f "$path" ]; then
			path="$(dirname "$path")"
		fi
		cd "$path"
	}

	alias pwdw='cygpath -wa .'

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
fi

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
	PROMPT_COMMAND='__git_ps1 "\[\e]0;\w\a\]\n\[\e[32m\]\u@\h \[\e[33m\]\w\[\e[0m\]" "\n$ "'
fi
