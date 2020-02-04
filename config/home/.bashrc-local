#!/bin/bash

# If not running interactively, don't do anything
[[ "$-" != *i* ]] && return

# https://stackoverflow.com/questions/3466166/how-to-check-if-running-in-cygwin-mac-or-linu://stackoverflow.com/questions/3466166/how-to-check-if-running-in-cygwin-mac-or-linux
case "$(uname -s)" in
    Linux*)     machine=Linux;;
    Darwin*)    machine=Mac;;
    CYGWIN*)    machine=Cygwin;;
    MINGW*)     machine=MinGw;;
    *)          machine="UNKNOWN:${unameOut}"
esac

set -o vi
bind -m vi-insert "\C-l":clear-screen
alias 'rgrep=grep -r --color=auto'
alias 'rg=rgrep'
alias 'rgi=rgrep -i'
alias '..=cd ..' # poor mans single level only substitute for fish's up one level shortcut
alias cdr='cd "$(readlink -f "$PWD")"'
alias td='tmux detach-client -a'
export EDITOR=vim
alias convert='gm convert'

lst()
{
	 ls -lht "$@"|head|tac
}

gg()
{
	if test -t 1; then
		git grep "$@" 2>/dev/null || grep -r --color=always "$@" | less -R -F -X
	else
		git grep "$@" 2>/dev/null || grep -r "$@" | less -F -X
	fi
}

if [ "$machine" = "Cygwin" ]; then
	cdw()
	{
		path="$(cygpath "$@")"
		if [ -f "$path" ]; then
			path="$(dirname "$path")"
		fi
		cd "$path"
	}

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
#else
#	curl -L https://raw.github.com/git/git/master/contrib/completion/git-prompt.sh > ~/.git-prompt.sh
fi
