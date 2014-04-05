#!/usr/bin/env python

from pluginmanager import notify, notify_exception
import subprocess

mappings = {
		# NOTE: Different versions of xsetwacom have different
		# mappings, yours may vary! If you don't have a "pad", try
		# "cursor" or upgrade:
		'Wacom Intuos3 9x12 pad': {
			#   +-----+-----+ +-------+   \    +-------+ +------+------+
			#   |     |     | |       |    \   |       | |      |      |
			#   |     |  1  | |  ^    |    /   |    ^  | |   9  |      |
			#   |     |     | |  |(4) |   /    | (4)|  | |      |      |
			#   |  3  +-----+ |  |    |   \    |    |  | +------+  11  |
			#   |     |     | |       |    \   |       | |      |      |
			#   |     |  2  | |       |    /   |       | |  10  |      |
			#   |     |     | |  |    |   /    |    |  | |      |      |
			#   +-----+-----+ |  |(5) |   \    | (5)|  | +------+------+
			#   |     8     | |  v    |    \   |    v  | |     12      |
			#   |           | |       |    /   |       | |             |
			#   +-----------+ +-------+   /    +-------+ +-------------+
			#
			# NOTE: BE SURE TO MAP THE STRIPS BEFORE THE BUTTONS
			# DUE TO A BUG IN THE WACOM STACK WHICH ERRANEOUSELY
			# MAPS BUTTONS 1-4 WHEN THE STRIPS ARE MAPPED

			'default': ( # Close to the default config from Windows
				('StripLeftUp',    'button 4'),
				('StripLeftDown',  'button 5'),
				('StripRightUp',   'key +ctrl button 4 key -ctrl'),
				('StripRightDown', 'key +ctrl button 5 key -ctrl'),

				('Button 1', 'key shift'),
				('Button 2', 'key alt'),
				('Button 3', 'key ctrl'),
				('Button 8', 'key +space'),

				('Button 9',  'key rshift'),
				('Button 10', 'key ralt'),
				('Button 11', 'key rctrl'),
				('Button 12', 'key +space'),
			),

			'gimp': (
				('StripLeftUp',    'button 4'),
				('StripLeftDown',  'button 5'),
				('StripRightUp',   'key +ctrl button 4 key -ctrl'),
				('StripRightDown', 'key +ctrl button 5 key -ctrl'),

				('Button 1', 'key ctrl z'),
				('Button 2', 'key alt'),
				('Button 3', 'key shift'),
				('Button 8', 'key ctrl'),

				('Button 9',  'key PgUp'),
				('Button 10', 'key PgDn'),
				('Button 11', 'key rctrl'),
				('Button 12', 'key +space'),
			),
		}
	}

@notify_exception
def apply_profile(device, profile):
	if device not in mappings:
		raise AttributeError('%s mapping not found' % device)
	if profile not in mappings[device]:
		raise AttributeError('%s profile for %s not found' % (profile, device))
	notify("Applying %s, %s profile" % (device, profile), 'wacom')

	# Work around a bug in the wacom stack causing the buttons to override
	# the strips (similar, but opposite to above bug note) by doing
	# everything twice:
	for i in range(2):
		for (prop, action) in mappings[device][profile]:
			# Wait for termination to avoid race:
			try:
				subprocess.call(['xsetwacom', 'set', device] + prop.split() + [action])
			except OSError:
				notify('xsetwacom not found', 'wacom')

if __name__ == '__main__':
    apply_profile('Wacom Intuos3 9x12 pad', 'gimp')
