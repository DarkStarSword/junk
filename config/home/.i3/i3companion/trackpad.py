#!/bin/echo Don't run me directly

trackpad = 'SynPS/2 Synaptics TouchPad' # HACK HACK HACK
trackpoint = 'TPPS/2 IBM TrackPoint'
enabled_prop = 'Device Enabled' # XXX Is this a standard name?

from pluginmanager import notify

import re
xinput_prop_spec = re.compile(r'''\s*(?P<prop_name>.+)\s\(\d+\):\s*(?P<val>\S)$''') # XXX This will break if parentheses can be in the value...
def get_xinput_prop(device, prop):
	import subprocess # TODO: Is there a python interface to xinput?
	xinput = subprocess.Popen(['xinput', '--list-props', device], stdout=subprocess.PIPE)
	for line in xinput.stdout:
		match = xinput_prop_spec.match(line)
		if not match:
			continue
		groups = match.groupdict()
		if groups['prop_name'] == prop:
			return groups['val']
	raise KeyError("Property not found in xinput's output")

def set_xinput_prop(device, prop, val):
	import subprocess # TODO: Is there a python interface to xinput?
	subprocess.check_output(map(str, ['xinput', '--set-prop', device, prop, val]))

def disable_device(device):
	set_xinput_prop(device, enabled_prop, 0)

def enable_device(device):
	set_xinput_prop(device, enabled_prop, 1)

def _toggle_device(device):
	enabled = int(get_xinput_prop(device, enabled_prop))
	if enabled:
		disable_device(device)
	else:
		enable_device(device)
	enabled = int(get_xinput_prop(device, enabled_prop))
	notify('%s %s' % (device, 'enabled' if enabled else 'disabled'), 'trackpad')

def toggle_trackpad():
	_toggle_device(trackpad)

def toggle_trackpoint():
	_toggle_device(trackpoint)

def toggle_device(device):
	{
		'trackpad': toggle_trackpad,
		'trackpoint': toggle_trackpoint,
	}[device]()
