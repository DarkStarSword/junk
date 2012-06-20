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
	bind B 'move-full-word back'
	bind w forward-word # FIXME: Should be start of next word
	bind W 'move-full-word next'
	bind e forward-word # FIXME: Should be end of next word
	bind E 'move-full-word end'
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

function vi_mode_insert -d "vi-like key bindings for fish (insert mode)"
	fish_default_key_bindings

	vi_mode_common

	bind \e vi_mode_normal
end
