#!/usr/bin/env python

import subprocess
import sys
module = sys.modules[__name__]
name = 'mocp'

from pluginmanager import notify_exception
import music

vol_delta = 5

if __name__ == '__main__':
	print "Don't call me directly"
	sys.exit(0)

def unload():
	music.unregister_music_backend(name)

def is_running():
	try:
		info = mocp_info()
		return True
	except (OSError, subprocess.CalledProcessError) as e:
		return False
	assert(False)

def mocp_info():
	output = subprocess.check_output('mocp -i'.split(), stderr=open('/dev/null', 'w')).split('\n')
	output = [ line.split(': ', 1) for line in output if line.split() ]
	return dict(output)

def is_playing():
	info = mocp_info()
	return info['State'] == 'PLAY'

def status():
	info = mocp_info()
	#print info
	if info['State'] == 'PLAY':
		tmp = ''
		if info['Artist']:
			tmp += '%s ' % info['Artist']
			if info['SongTitle']:
				tmp += '- '
		if info['SongTitle']:
			tmp += '%s ' % info['SongTitle']
		else:
			tmp += '%s ' % info['File']
		return '%s[%s]' % (tmp, info['CurrentTime'])
	return None

def mocp_state():
	return mocp_info()['State']

def mocp_command(*args):
	subprocess.check_call(['mocp'] + list(args))

def play_pause():
	state = mocp_state()
	if state == 'STOP':
		mocp_command('-p') # Play
	else:
		mocp_command('-G') # Play/Pause

def next_track():
	state = mocp_state()
	if state == 'STOP':
		mocp_command('-p') # Play
	else:
		mocp_command('-f') # Next

def mute():
	return 'mute unimplemented'

commands = {
	'Play': lambda: mocp_command('-p'),
	'Play/Pause': play_pause,
	'Stop': lambda: mocp_command('-s'),
	'Previous Track': lambda: mocp_command('-r'),
	'Next Track': next_track,
	'Volume Up': lambda: mocp_command('-v', '+%i' % vol_delta),
	'Volume Down': lambda: mocp_command('-v', '-%i' % vol_delta),
	'Mute': mute
}

music.register_music_backend(name, module)
