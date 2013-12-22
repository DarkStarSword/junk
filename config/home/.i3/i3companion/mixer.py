from pluginmanager import notify, notify_exception

mixer_delta = 2
pulse_adjust_factor = 0.01
mixers = [] # Set this in local.py to adjust non-default or multiple mixers

def def_mixer():
	# This must be instantiated every time to get the current values of the
	# mixer, in case they have been changed externally
	import alsaaudio
	if len(mixers):
		return alsaaudio.Mixer(mixers[0])
	else:
		return alsaaudio.Mixer()

def slave_mixers():
	import alsaaudio
	return [ alsaaudio.Mixer(mixer) for mixer in mixers[1:] ]

def sync_mixers(vol = None, mute = None):
	import alsaaudio
	ret = []
	for m in slave_mixers():
		name = None
		if vol is not None:
			m.setvolume(vol)
			name = m.mixer()
		if mute is not None:
			try:
				m.setmute(mute)
				name = m.mixer()
			except alsaaudio.ALSAAudioError:
				# No mute switch?
				pass
		if name is not None:
			ret += [name]
	return ret

def alsa_vol(adjust):
	# FIXME: This is not the same scale as used by alsamixer
	m = def_mixer()
	nv = ov = m.getvolume()[0]
	small_adjust = adjust / abs(adjust)

	v = ov + adjust
	if v > 100: v = 100
	elif v < 0: v = 0

	while nv == ov:
		m.setvolume(v)
		nv = m.getvolume()[0]
		v = v + small_adjust
		if v > 100 or v < 0:
			break
	try:
		mute = m.getmute()[0] and ' [MUTE]' or ''
	except:
		mute = ''

	names = ', '.join([ m.mixer() ] + sync_mixers(vol=nv))
	notify("%s: %d%%%s" % (names, nv, mute), key='mixer')

def pulse_vol(adjust):
	import pulse
	v = pulse.PulseAppVolume()
	(vol, mute) = v(None, adjust * pulse_adjust_factor)
	mute = mute and ' [MUTE]' or ''
	notify("Mixer: %d%%%s" % (vol / pulse_adjust_factor, mute), key='mixer')

def vol(adjust):
	try:
		pulse_vol(adjust)
	except:
		alsa_vol(adjust)

def vol_up(): return vol(mixer_delta)
def vol_down(): return vol(-mixer_delta)

@notify_exception
def intel_vol(command):
	try:
		import music
		if music.is_playing():
			# NOTE: These commands are executed async, so we can't
			# catch errors here. The music plugin will direct the
			# request back to us if it can't handle it.
			if command in ('up', 'down'):
				music.command('Volume %s' % command.title())
			else:
				music.command(command.title())
			return
	except ImportError:
		pass

	globals()['vol_%s'%command]()

def intel_vol_up(): return intel_vol('up')
def intel_vol_down(): return intel_vol('down')
def intel_vol_mute(): return intel_vol('mute')

def alsa_vol_mute():
	m = def_mixer()
	v = m.getmute()[0]
	v = not v
	m.setmute(v)

	names = ', '.join([ m.mixer() ] + sync_mixers(mute=v))
	notify("%s: %s" % (names, 'MUTE' if m.getmute()[0] else 'on'), key='mixer')

def pulse_vol_mute():
	import pulse
	v = pulse.PulseAppVolume()
	(vol, mute) = v(None, toggle_mute=True)
        notify('Mixer: MUTE' if mute else 'Mixer: on', key='mixer')

def vol_mute():
	try:
		pulse_vol_mute()
	except:
		alsa_vol_mute()
