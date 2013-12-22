#!/usr/bin/env python

import subprocess
import sys
module = sys.modules[__name__]
name = 'cmus'

from pluginmanager import notify_exception
import music

vol_delta = 5
_last_vol = 100

if __name__ == '__main__':
	print "Don't call me directly"
	sys.exit(0)

def unload():
	music.unregister_music_backend(name)

def is_running():
	try:
		info = cmus_info()
		return True
	except (OSError, subprocess.CalledProcessError) as e:
		return False
	assert(False)

def cmus_info():
	output = subprocess.check_output('cmus-remote -Q'.split(), stderr=open('/dev/null', 'w')).split('\n')
	tags = {}
	status = {}
	settings = {}
	for item in map(str.split, output):
		if len(item) > 2 and item[0] == 'tag':
			tags[item[1]] = ' '.join(item[2:])
		elif len(item) > 2 and item[0] == 'set':
			settings[item[1]] = ' '.join(item[2:])
		elif len(item) > 1 and item[0] in 'status file duration position'.split():
			status[item[0]] = ' '.join(item[1:])
	return (status, tags, settings)

def is_playing():
	(status, tags, _) = cmus_info()
	return status['status'] == 'playing'

def fmt_time(seconds):
	seconds = int(seconds)
	mins = seconds / 60
	secs = seconds % 60
	hrs  = mins / 60
	mins = mins % 60
	if hrs:
		return '%d:%.2d:%.2d' % (hrs, mins, secs)
	else:
		return '%d:%.2d' % (mins, secs)

def status():
	(status, tags, _) = cmus_info()
	#print (status, tags)
	if status['status'] == 'playing':
		tmp = ''
		if 'artist' in tags and tags['artist']:
			tmp += '%s ' % tags['artist']
			if 'title' in tags and tags['title']:
				tmp += '- '
		if 'title' in tags and tags['title']:
			tmp += '%s ' % tags['title']
		else:
			tmp += '%s ' % status['file']
		return '%s[%s/%s]' % (tmp, fmt_time(status['position']), fmt_time(status['duration']))
	return None

def cmus_command(*args):
	subprocess.check_call(['cmus-remote'] + list(args))

def _cmus_vol():
	(_, _, settings) = cmus_info()
	l = settings['vol_left']
	r = settings['vol_right']
	return map(int, (l, r))

def cmus_vol(delta):
	cmus_command('-v', delta)
	(l, r) = _cmus_vol()
	if l == r:
		return '%s%%' % l
	return 'L:%s%% R:%s%%' % (l,r)

def mute():
	global _last_vol

	v = min(_cmus_vol())
	if v:
		_last_vol = v
		cmus_command('-v', '0%')
	else:
		cmus_command('-v', '%d%%' % _last_vol)
		return '%s%%' % _last_vol

def play_pause():
	cmus_command('-u');
	(status, _, _) = cmus_info()
	return status['status'].title()

commands = {
	'Play': lambda: cmus_command('-p'),
	'Play/Pause': play_pause,
	'Stop': lambda: cmus_command('-s'),
	'Previous Track': lambda: cmus_command('-r'),
	'Next Track': lambda: cmus_command('-n'),
	'Volume Up': lambda: cmus_vol('+%i%%' % vol_delta),
	'Volume Down': lambda: cmus_vol('-%i%%' % vol_delta),
	'Mute': mute,
}

music.register_music_backend(name, module)
