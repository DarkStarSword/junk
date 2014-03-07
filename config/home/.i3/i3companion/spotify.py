#!/usr/bin/env python

import subprocess
import sys
module = sys.modules[__name__]
name = 'spotify'

from pluginmanager import notify_exception
import music
import wmiidbus
import dbus

vol_delta = 0.05

def unload():
	music.unregister_music_backend(name)

_spotify = None
def get_spotify_interface():
	global _spotify

	bus = wmiidbus.get_session_bus()

	if _spotify is not None and bus.name_has_owner(_spotify._named_service):
		return _spotify

	# NOTE: Spotify exports two usable interfaces:
	# org.freedesktop.MediaPlayer2 interface under /
	# org.mpris.MediaPlayer2.Player interface under /org/mpris/MediaPlayer2
	# The latter exports PlaybackStatus, which I don't see an equivelant of
	# in the former. The former does export volume controls, but they don't
	# seem to work for me (possibly because I'm using pulseaudio &
	# bluetooth?)
	_spotify = bus.get_object('com.spotify.qt', '/org/mpris/MediaPlayer2')
	return _spotify

def is_running():
	try:
		spotify = get_spotify_interface()
		return True
	except dbus.DBusException:
		return False

def spotify_info():
	spotify = get_spotify_interface()
	#m = spotify.GetMetadata() # org.freedesktop.MediaPlayer2 API
	m = spotify.Get('org.mpris.MediaPlayer2.Player', 'Metadata')
	# return { str(x): str(m[x][0]) if isinstance(m[x], dbus.Array) else str(m[x]) for x in m }
	return dict([ (str(x), str(m[x][0]) if isinstance(m[x], dbus.Array) else str(m[x])) for x in m ])

def is_playing():
	try:
		spotify = get_spotify_interface()
		return spotify.Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus') == 'Playing'
	except dbus.DBusException:
		return False

def _status():
	(artist, title) = (None, None)
	metadata = spotify_info()
	if metadata == {}:
		spotify_pulse_mute(True)
		return 'NO METADATA - ASSUMING AD AND MUTING'
	tmp = ''
	if 'xesam:artist' in metadata and metadata['xesam:artist']:
		artist = metadata['xesam:artist']
		tmp += '%s ' % artist
		if 'xesam:title' in metadata and metadata['xesam:title']:
			tmp += '- '
	if 'xesam:title' in metadata and metadata['xesam:title']:
		title = metadata['xesam:title']
		tmp += '%s ' % title
	return tmp
	#return '%s[%s/%s]' % (tmp, status['position'], status['duration'])

def status():
	# TODO: Since we don't have times, we would be better off subscribing
	# to the track change dbus notification and skipping the constant
	# polling
	if is_playing():
		return _status()
	return None

def spotify_command(command):
	spotify = get_spotify_interface()
	getattr(spotify, command)()

def spotify_pulse_vol(delta):
	# TODO: If spotify is not connected, redirect command back to mixer
	import pulse
	(vol, mute) = pulse.PulseAppVolume()('Spotify', vol_delta=delta)
	return '%.0f%%' % (vol*100.0)

def spotify_pulse_mute(mute=None):
	# TODO: If spotify is not connected, redirect command back to mixer
	import pulse
	toggle_mute = mute == None
	(vol, mute) = pulse.PulseAppVolume()('Spotify', toggle_mute=toggle_mute, mute=mute)
	if not mute:
		return '%.0f%%' % (vol*100.0)

commands = {
	'Play': lambda: spotify_command('Play'),
	'Play/Pause': lambda: spotify_command('PlayPause'),
	'Stop': lambda: spotify_command('Stop'),
	'Previous Track': lambda: spotify_command('Previous'),
	'Next Track': lambda: spotify_command('Next'),
	'Volume Up': lambda: spotify_pulse_vol(vol_delta),
	'Volume Down': lambda: spotify_pulse_vol(-vol_delta),
	'Mute': lambda: spotify_pulse_mute(),
}

if __name__ == '__main__':
	print
	print _status()
	print # pygmi usually runs into a threading issue while shutting down
	wmiidbus.unload()
	sys.exit(0)
else:
	music.register_music_backend(name, module)
