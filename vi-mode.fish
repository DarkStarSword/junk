function fish_key_bindings_emacs -d "emacs key bindings between modes"

	# This is straight out the the fish default bindings (for now)

	# Clear earlier bindings, if any
	bind --erase --all

	# This is the default binding, i.e. the one used if no other binding matches
	bind "" self-insert

	bind \n execute

	bind \ck kill-line
	bind \cy yank
	bind \t complete

	bind \e\n "commandline -i \n"

	bind \e\[A up-or-search
	bind \e\[B down-or-search
	bind -k down down-or-search
	bind -k up up-or-search

	bind \e\[C forward-char
	bind \e\[D backward-char
	bind -k right forward-char
	bind -k left backward-char

	bind -k dc delete-char
	bind -k backspace backward-delete-char
	bind \x7f backward-delete-char

	bind \e\[H beginning-of-line
	bind \e\[F end-of-line
	bind -k home beginning-of-line
	bind -k end end-of-line

	bind \e\eOC nextd-or-forward-word
	bind \e\eOD prevd-or-backward-word
	bind \e\e\[C nextd-or-forward-word
	bind \e\e\[D prevd-or-backward-word
	bind \eO3C nextd-or-forward-word
	bind \eO3D prevd-or-backward-word
	bind \e\[3C nextd-or-forward-word
	bind \e\[3D prevd-or-backward-word
	bind \e\[1\;3C nextd-or-forward-word
	bind \e\[1\;3D prevd-or-backward-word

	bind \e\eOA history-token-search-backward
	bind \e\eOB history-token-search-forward
	bind \e\e\[A history-token-search-backward
	bind \e\e\[B history-token-search-forward
	bind \eO3A history-token-search-backward
	bind \eO3B history-token-search-forward
	bind \e\[3A history-token-search-backward
	bind \e\[3B history-token-search-forward
	bind \e\[1\;3A history-token-search-backward
	bind \e\[1\;3B history-token-search-forward

	bind \ca beginning-of-line
	bind \ce end-of-line
	bind \ey yank-pop
	bind \ch backward-delete-char
	bind \cw backward-kill-word
	bind \cp history-search-backward
	bind \cn history-search-forward
	bind \cf forward-char
	bind \cb backward-char
	bind \e\x7f backward-kill-word
	bind \eb backward-word
	bind \ef forward-word
	bind \e\[1\;5C forward-word
	bind \e\[1\;5D backward-word
	bind \ed forward-kill-word
	bind -k ppage beginning-of-history
	bind -k npage end-of-history
	bind \e\< beginning-of-buffer
	bind \e\> end-of-buffer

	bind \el __fish_list_current_token
	bind \ew 'set tok (commandline -pt); if test $tok[1]; whatis $tok[1]; commandline -f repaint; end'
	bind \cl 'clear; commandline -f repaint'
	bind \cc 'commandline ""'
	bind \cu backward-kill-line
	bind \ed kill-word
	bind \cw backward-kill-word
	bind \ed 'if test -z (commandline); dirh; commandline -f repaint; else; commandline -f kill-word; end'
	bind \cd delete-or-exit

	# This will make sure the output of the current command is paged using the less pager when you press Meta-p
	bind \ep '__fish_paginate'

end

function move-full-word
	# FIXME: This is nasty
	#
	# No way to get unescaped commandline AFAICT, so commandline -C may not
	# actually bear any relevance to commandline... fail.
	#
	# This is close to correct, but without being able to get the unescaped
	# command line there will always be corner cases that will do the wrong
	# thing, particularly where quotes are involved.

	set direction $argv[1]
	set full_cmdline (commandline)
	set part_cmdline (commandline -c)
	set pos (commandline -C)

	# Embedded python... If you can do this in pure shell then more power to you :)
	commandline -C (python -c "
full_cmdline = '$full_cmdline'
part_cmdline = '$part_cmdline'[:-1]
real_pos = int('$pos')
stupid_pos = 0 if real_pos == 0 else len(part_cmdline) + 1

if '$direction' == 'next':
	new_pos = full_cmdline.find(' ', stupid_pos + 1)
	if new_pos < 0:
		new_pos = len(full_cmdline)
	new_pos = real_pos - stupid_pos + new_pos + 1
if '$direction' == 'end':
	new_pos = full_cmdline.find(' ', stupid_pos + 3)
	if new_pos < 0:
		new_pos = len(full_cmdline)
	new_pos = real_pos - stupid_pos + new_pos - 1
elif '$direction' == 'back':
	new_pos = real_pos - stupid_pos + part_cmdline.rfind(' ') + 1
	if new_pos < 0:
		new_pos = 0
print new_pos
	")
end

function backward-full-word
	move-full-word back
end

function forward-full-word
	move-full-word next
end

function forward-full-word-end
	move-full-word end
end

function vi_mode_common -d "common key bindings for all vi-like modes"
	bind \cc 'echo; commandline ""; vi_mode_normal' # Breaks if multiline commandline
	bind \cd delete-or-exit
end

function vi_mode_normal -d "WIP vi-like key bindings for fish (normal mode)"
	bind --erase --all

	vi_mode_common

	bind \n "commandline -f execute; vi_mode_insert"

	bind i vi_mode_insert
	bind I 'commandline -f beginning-of-line; vi_mode_insert'
	bind a 'commandline -f forward-char; vi_mode_insert'
	bind A 'commandline -f end-of-line; vi_mode_insert'

	bind j history-search-forward
	bind k history-search-backward

	bind h backward-char
	bind l forward-char
	bind b backward-word # Note: this implementation is buggy. Try using b from the end of 'echo hi' to see what I mean
	bind B backward-full-word
	bind w forward-word # FIXME: Should be start of next word
	bind W forward-full-word
	bind e forward-word # FIXME: Should be end of next word
	bind E forward-full-word-end
	bind 0 beginning-of-line
	bind _ beginning-of-line
	bind \$ end-of-line

	bind x delete-char
	bind D kill-line
	# bind Y 'commandline -f kill-whole-line yank'
	bind P yank
	bind p 'commandline -f yank forward-char' # Yes, this is reversed. Otherwise it does the wrong thing. Go figure.
	bind C 'commandline -f kill-line; vi_mode_insert'
	bind S 'commandline -f kill-whole-line; vi_mode_insert'

	# NOT IMPLEMENTED:
	# bind 2 vi-arg-digit
	# bind d delete-direction
	# bind c change-direction
	# bind s substitude-direction
	# bind y yank-direction
	# bind r replace
	# bind R overwrite
	# bind g magic :-P
	# bind u undo
	# bind f find
	# bind F find-prev
	# bind t till
	# bind T till-prev
	# bind o insert on new line below
	# bind O insert on new line above
	# bind ^a increment next number
	# bind ^a increment next number
	# bind /?nN search (jk kind of does this)
	# etc.
end


# bind --function-names (readline commands):
#
# beginning-of-line
# end-of-line
# forward-char
# backward-char
# forward-word
# backward-word
# history-search-backward
# history-search-forward
# delete-char
# backward-delete-char
# kill-line
# yank
# yank-pop
# complete
# beginning-of-history
# end-of-history
# backward-kill-line
# kill-whole-line
# kill-word
# backward-kill-word
# dump-functions
# history-token-search-backward
# history-token-search-forward
# self-insert
# null
# eof
# vi-arg-digit
# execute
# beginning-of-buffer
# end-of-buffer
# repaint
# up-line
# down-line

function vi_mode_insert -d "vi-like key bindings for fish (insert mode)"
	fish_key_bindings_emacs

	vi_mode_common

	bind \e vi_mode_normal
end
