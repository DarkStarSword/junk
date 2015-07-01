#!/usr/bin/env

import mixer
import music
import trackpad
import randr
import upower
import consolekit
import systemd

def activate_key_bindings(keybinder):
	"""
	This is a stub that sets up a hard coded set of keybindings.
	It needs to be replaced with something that parses a config file.
	Patches welcome.
	"""

	Ctrl = keybinder.Control
	Shift = keybinder.Shift
	Alt = keybinder.Alt
	Win = keybinder.Win
	mod = Win

	keybinder.bind_key(0,        'XF86_AudioLowerVolume', mixer.intel_vol_down)
	keybinder.bind_key(mod,      'XF86_AudioLowerVolume', mixer.vol_down)
	keybinder.bind_key(mod,      'bracketleft',          mixer.intel_vol_down)
	keybinder.bind_key(mod|Ctrl, 'bracketleft',          mixer.vol_down)
	keybinder.bind_key(0,        'XF86_AudioRaiseVolume', mixer.intel_vol_up)
	keybinder.bind_key(mod,      'XF86_AudioRaiseVolume', mixer.vol_up)
	keybinder.bind_key(mod,      'bracketright',         mixer.intel_vol_up)
	keybinder.bind_key(mod|Ctrl, 'bracketright',         mixer.vol_up)
	keybinder.bind_key(0,        'XF86_AudioMute',        mixer.intel_vol_mute)
	keybinder.bind_key(mod,      'XF86_AudioMute',        mixer.vol_mute)
	keybinder.bind_key(mod,      'backslash',            mixer.intel_vol_mute)
	keybinder.bind_key(mod|Ctrl, 'backslash',            mixer.vol_mute)


	keybinder.bind_key(0,     'XF86_TouchpadToggle', trackpad.toggle_trackpad)
	keybinder.bind_key(Shift, 'XF86_TouchpadToggle', trackpad.toggle_trackpoint)
	keybinder.bind_key(mod,   'F8', trackpad.toggle_trackpad)
	keybinder.bind_key(mod|Shift,'F8', trackpad.toggle_trackpoint)
	keybinder.bind_key(0,     'XF86_AudioPrev',      music.prev)
	keybinder.bind_key(0,     'XF86_AudioPlay',      music.pause)
	keybinder.bind_key(0,     'XF86_AudioPause',     music.pause)
	keybinder.bind_key(0,     'XF86_AudioStop',      music.stop)
	keybinder.bind_key(0,     'XF86_AudioNext',      music.next)
	keybinder.bind_key(mod,   'z',                  music.prev)
	keybinder.bind_key(mod,   'x',                  music.play)
	keybinder.bind_key(mod,   'c',                  music.pause)
	keybinder.bind_key(mod,   'v',                  music.stop)
	keybinder.bind_key(mod,   'b',                  music.next)

	keybinder.bind_key(mod,   'Up',                 randr.raise_brightness)
	keybinder.bind_key(mod,   'Down',               randr.lower_brightness)
	keybinder.bind_key(mod|Shift,'Up',              upower.raise_kbd_backlight)
	keybinder.bind_key(mod|Shift,'Down',            upower.lower_kbd_backlight)

	randr.register_xf86_keys(keybinder)
        try:
            systemd.register_xf86_keys(keybinder)
            # Additional binding for thinkpad where power button notification
            # does not get through to X (not even /dev/input or acpi):
            keybinder.bind_key(0, 'XF86_Launch1', systemd.power_button)
        except:
            upower.register_xf86_keys(keybinder)
            consolekit.register_xf86_keys(keybinder)
