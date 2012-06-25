function direction_command
	# Embedded python... If you can do this in pure shell then more power to you :)

	# There may be some speedup to be gained by splitting this out into a
	# separate script, which python can compile once instead of every time

	set ret (python -c "

import sys
command = sys.argv[1]
direction = sys.argv[2]
new_pos = pos = int(sys.argv[3])
cmdline = '\n'.join(sys.argv[4:])

def start():
	return (0, 0)
def end():
	return (len(cmdline), -1)

dir_0 = dir__ = start # FIXME: start of line/first non-whitespace char in line, not entire cmdline
dir_eol = end # FIXME: end of line, not entire cmdline

# These three routines are similar, they can probably be combined into one, but
# I'll make sure I get all working and understand the differences first
def _dir_w(regexp):
	import re

	searchpart = cmdline[pos:]
	match = re.search(regexp, searchpart)
	if not match:
		return end()
	return (pos + match.end()-1, 0)

def _dir_e(regexp):
	import re

	searchpart = cmdline[pos+1:]
	match = re.search(regexp, searchpart)
	if not match:
		return end()
	return (pos+2 + match.start(), -1)

def _dir_b(regexp):
	import re

	if pos == 0:
		return start()

	searchpart = cmdline[:pos]
	match = re.search(regexp, searchpart)
	if not match:
		return start()
	return (match.start()+1, 0)

# Simple, but not inclusive enough:
# def dir_w(): return _dir_w(r'[^\w]\w')
# def dir_e(): return _dir_e(r'\w[^\w]')
# def dir_b(): return _dir_b(r'[^\w]\w+[^\w]*\$') # NOTE: \$ has to be escaped here since we are in a quote inside a fish script

# Slightly too inclusive, e.g. fi--sh matches both '-' characters, but should only match one:
def dir_w(): return _dir_w(r'[^\w][^\s]|\w[^\w\s]')
def dir_e(): return _dir_e(r'[^\s][^\w]|[^\w\s]\w')
# Also, by the time I got to writing this one my brain had already imploded:
def dir_b(): return _dir_b(r'([^\w][^\s]|\w[^\w\s])\w*[^\w]*\$') # NOTE: \$ has to be escaped here

def dir_W(): return _dir_w(r'\s[^\s]')
def dir_E(): return _dir_e(r'[^\s]\s')
def dir_B(): return _dir_b(r'\s[^\s]+\s*\$') # NOTE: \$ has to be escaped here

def dir_h():
	if pos: return (pos-1, 0)
	return start()

def dir_l():
	return (pos+1, 0)

def dir_t(char):
	new_pos = cmdline.find(char, pos+1)
	if new_pos < 0:
		return (pos, 0)
	return (new_pos, -1)

def dir_T(char):
	new_pos = cmdline.rfind(char, 0, pos)
	if new_pos < 0:
		return (pos, 0)
	return (new_pos+1, 0)

def dir_f(char): return (dir_t(char)[0]+1, -1)
def dir_F(char): return (dir_T(char)[0]-1, 0)

def cmd_d():
	dst_pos = dir(direction)
	if dst_pos >= pos:
		new_cmdline = cmdline[:pos] + cmdline[dst_pos:]
		return (new_cmdline, pos)
	new_cmdline = cmdline[:dst_pos] + cmdline[pos:]
	return (new_cmdline, dst_pos)
cmd_c = cmd_d

def dir(d, cursor = False):
	a = ()
	if ':' in d:
		(d, a) = d.split(':', 1)
	(new_pos, cursor_off) = globals()['dir_%s' % d](*a)
	if cursor:
		return new_pos + cursor_off
	return new_pos

def cmd(c): return globals()['cmd_%s' % c]()

if command == ' ':
	new_pos = dir(direction, True)
else:
	(cmdline, new_pos) = cmd(command)

print cmdline
print new_pos

" $argv[1] $argv[2] (commandline -C) (commandline)) # commandline should always be last

	set new_pos $ret[-1]
	set -e ret[-1] # Guessing that deleting last element is likely to be faster than deleting first
	commandline $ret
	commandline -C $new_pos
end

function vi_mode_common -d "common key bindings for all vi-like modes"
	bind \e vi_mode_normal
	bind \cc 'echo; commandline ""; vi_mode_insert' # Breaks if multiline commandline
	bind \cd delete-or-exit
	bind \cl 'clear; commandline -f repaint'
end

function vi_mode_common_insert -d "common key bindings for all insert vi-like modes"
	vi_mode_common
	bind \e 'commandline -f backward-char; vi_mode_normal'
end

function bind_directions
	vi_mode $argv[1]

	for direction in W w E e B b 0 _ h l
		bind $direction "direction_command '$argv[1]' $direction; $argv[2]"
	end
	bind \$ "direction_command '$argv[1]' eol; $argv[2]"
	for direction in f F t T
		bind $direction "bind_all 'direction_command %q$argv[1]%q {$direction}:%k; $argv[2]'"
	end
end

function bind_all
	# There seems to be some magic that doesn't work properly without this:
	bind '' self-insert

	python -c "
command = '''$argv'''
for c in map(chr, range(0x20, 0x7f)):
	q = '\"' # Enclose command in these
	Q = '\'' # Other quote - for quotes inside command
	if c == '\"':
		l = r = r'\\%s' % c
		(q, Q) = (Q, q) # Swap quotes
	elif c in ['(', ')', '<', '>', ';', '|', '\'']:
		l = r = r'\%s' % c
	elif c == '\\\\':
		l = r'\\\\'
		r = r'\\\\\\\\'
	elif c == '\$':
		l = '\%s' % c
		r = r\"'\%s'\" % c
	else:
		l = r = \"'%s'\" % c
	print '''bind %s %s%s%s''' % (l, q, command.replace('%k', r).replace('%q', Q), q)
" | .
end

function vi_mode
	set -g vi_mode $argv
	commandline -f repaint
end

function replace
	vi_mode 'r'
	bind --erase --all
	vi_mode_common

	# backward-char should happen last, but only works if specified first
	# (guess I should dig through the C code and figure out what is going
	# on):
	# bind_all "commandline -f delete-char; commandline -i %k; commandline -f backward-char; vi_mode_normal"
	bind_all "commandline -f backward-char delete-char; commandline -i %k; vi_mode_normal"

end

function overwrite
	vi_mode 'R'
	bind --erase --all
	vi_mode_common_insert

	bind_all "commandline -f delete-char; commandline -i %k"
end

function vi_mode_normal -d "WIP vi-like key bindings for fish (normal mode)"
	vi_mode ' '

	bind --erase --all

	# NOTE: bind '' self-insert seems to be required to allow the
	# prompt to change, but we don't want unbound keys to be able to
	# self-insert, so set the default binding, but bind everything to
	# do nothing (which is wasteful, but seems to work):
	bind_all ''

	vi_mode_common

	bind \n "commandline -f execute; vi_mode_insert"

	bind i vi_mode_insert
	bind I 'commandline -f beginning-of-line; vi_mode_insert'
	bind a 'commandline -f forward-char; vi_mode_insert'
	bind A 'commandline -f end-of-line; vi_mode_insert'

	bind j history-search-forward
	bind k history-search-backward

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

	bind_directions ' ' vi_mode_normal
	bind d 'bind_directions d vi_mode_normal'
	bind c 'bind_directions c vi_mode_insert'

	# Override generic direction code for simple things that have a close
	# match in fish's builtin commands, which should be faster:
	bind h backward-char
	bind l forward-char
	bind 0 beginning-of-line
	bind _ beginning-of-line
	bind \$ end-of-line
	# bind b backward-word # Note: built-in implementation is buggy (patch submitted). Also, before enabling this override, determine if this matches on the right characters

	# NOT IMPLEMENTED:
	# bind 2 vi-arg-digit
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
	# registers (maybe try to make sensible integration into X, like an
	#   explicit yank with y goes to an X selection, while an implicit
	#   delete with x etc. doesn't. "* and "+ should natually go to the
	#   appropriate X selection if possible)
	# etc.
end

function vi_mode_insert -d "vi-like key bindings for fish (insert mode)"
	vi_mode 'I'

	fish_default_key_bindings

	vi_mode_common_insert
end
