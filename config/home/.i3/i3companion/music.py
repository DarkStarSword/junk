#!/usr/bin/env python

import pluginmanager
from pluginmanager import notify, notify_exception, async

autoloadMusicBackends = ['moc', 'cmus', 'spotify']
registeredMusicBackends = {}
last_music_player = None

if __name__ == '__main__':
	import sys
	print "Don't call me directly"
	sys.exit(0)

def unload():
	global registeredMusicBackends
	for module in registeredMusicBackends.values():
		pluginmanager.cleanup_plugin(module)
	try:
		assert(registeredMusicBackends == {})
	finally:
		registeredMusicBackends = {}
		music_status.active = False

@notify_exception
def register_music_backend(name, module):
	assert(name not in registeredMusicBackends)
	registeredMusicBackends[name] = module

@notify_exception
def unregister_music_backend(name):
	global last_music_player

	if last_music_player == name:
		last_music_player = None
	if name in registeredMusicBackends:
		del registeredMusicBackends[name]

def music_player_running():
	global last_music_player

	running = {}
	for (name, module) in registeredMusicBackends.items():
		if module.is_running():
			running[name] = module

	for (name, module) in running.items():
		if module.is_playing():
			last_music_player = name
			return (name, module)

	if running == {}:
		last_music_player = None
		return (None, None)
	elif last_music_player not in running:
		last_music_player = running.keys()[0]
	return (last_music_player, running[last_music_player])

def is_playing():
	(name, player) = music_player_running()
	if player is None:
		return False
	return player.is_playing()

@async
@notify_exception
def command(command):
	(name, player) = music_player_running()
	if player is None:
		notify('No supported music player running')
		music_status.active = False
		return

	if command not in player.commands:
		if command in ['Volume Up', 'Volume Down', 'Mute']:
			import mixer
			# This redirection is getting silly... XF86Keys ->
			# mixer -> music -> mixer... and every time we change
			# the name of the command...
			getattr(mixer, 'vol_%s'%command.split()[-1].lower())()
		else:
			notify('%s: Unimplemented' % name)
		return

	ret = player.commands[command]()
	if ret is not None:
		notify('%s: %s' % (name, ret), key='music')
	else:
		notify('%s: %s' % (name, command), key='music')

	init_status(player)

def prev(): return command('Previous Track')
def play(): return command('Play')
def pause(): return command('Play/Pause')
def stop(): return command('Stop')
def next(): return command('Next Track')

@notify_exception
def music_status(self):
	if not hasattr(self, 'status') or not hasattr(self, 'status_failures'):
		return None # Not initialised yet
	try:
		status = self.status()
	except:
		self.status_failures += 1
		if self.status_failures > 60:
			notify('Too many failures getting music player status')
			self.status_failures = 0
			self.active = False
		return None
	self.status_failures = 0
	if status:
		return status
	return None
music_status.active = False
music_status.status_failures = 0

@notify_exception
def init_status(player = None):
	global last_music_player

	if player is None:
		(name, player) = music_player_running()
		if player is None:
			return
	if isinstance(player, str): # launch passes the player name, which may not have finished init yet
		player = registeredMusicBackends[player]

	if last_music_player and \
			last_music_player != player.name and \
			registeredMusicBackends[last_music_player].is_playing():
		return

	last_music_player = player.name

	if hasattr(player, 'status'):
		music_status.status = player.status
		if not music_status.active:
			music_status.active = True

def init():
	for plugin in autoloadMusicBackends:
		__import__(plugin)

init()
# try: init_status()
# except: pass
