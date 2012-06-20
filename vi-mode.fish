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
part_cmdline = '$part_cmdline'
real_pos = int('$pos')
stupid_pos = len(part_cmdline)

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
	new_pos = real_pos - stupid_pos + part_cmdline.rfind(' ', 0, stupid_pos-1) + 1
	if new_pos < 0:
		new_pos = 0
print new_pos
	")
end

function vi_mode_common -d "common key bindings for all vi-like modes"
	bind \e vi_mode_normal
	bind \cc 'echo; commandline ""; vi_mode_insert' # Breaks if multiline commandline
	bind \cd delete-or-exit
end

function replace
	bind --erase --all
	vi_mode_common

	# Annoyingly, the pressed key does not seem to be passed to the called
	# function (unless it is the builtin self-insert), so I need to bind
	# each and every damn key I'm interested in:
	for char in (python -c "for c in range(0x20, 0x7f): print chr(c)")
		bind "$char" "commandline -f delete-char; commandline -i '$char'; vi_mode_normal"
	end
end

function overwrite
	bind --erase --all
	vi_mode_common

	# Can someone please explain why this doesn't work, yet the almost
	# identical replace function does? Why does returning to normal mode
	# allow delete-char to work?
	for char in (python -c "for c in range(0x20, 0x7f): print chr(c)")
		bind "$char" "commandline -f delete-char; commandline -i '$char'"
	end
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
	bind s 'commandline -f delete-char; vi_mode_insert'
	bind r replace
	bind R overwrite

	# NOT IMPLEMENTED:
	# bind 2 vi-arg-digit
	# bind d delete-direction
	# bind c change-direction
	# bind y yank-direction
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
end
