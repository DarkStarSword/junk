#!/bin/bash

script_dir_rel="$(dirname "$0")"
script_dir_abs="$(realpath "$script_dir_rel")"

linkit()
{
	link_sub_dir="$(dirname "$@")"
	if [ "$link_sub_dir" != "." ]; then
		mkdir -p "$HOME/$link_sub_dir"
	fi
	rel_target="$(realpath --relative-to="$HOME/$link_sub_dir" "$script_dir_abs/$@")"
	ln -sv "$rel_target" "$HOME/$@"
}

# Files I want linked up for every install:
linkit ".bash_aliases"
linkit ".config/nvim/init.vim"
linkit ".tmux.conf"
linkit ".vimrc"

# Other files are more situational
