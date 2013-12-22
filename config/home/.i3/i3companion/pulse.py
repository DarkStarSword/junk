#!/usr/bin/env python

# Veromix & Earcandy both feature more complete python bindings around
# PulseAudio. It would be nice if one of them split it out into a separately
# maintained library, but for now I'm just importing lib_pulseaudio.py (a
# python translation of the pulseaudio header files) from one of them (veromix,
# because it has been updated more recently than earcandy) and implementing the
# minimum I need to control a particular stream's volume.

# Useful PulseAudio documentation may be found at:
# http://www.freedesktop.org/software/pulseaudio/doxygen/index.html
#  (That's not a real "index", and I haven't managed to find one)
# http://www.freedesktop.org/software/pulseaudio/doxygen/async.html
# http://www.freedesktop.org/software/pulseaudio/doxygen/introspect.html
# http://www.freedesktop.org/software/pulseaudio/doxygen/volume.html

from pulseaudio import lib_pulseaudio as _lib

class PulseAppVolume(object):
	def __call__(self, app_name, vol_delta=None, toggle_mute=False, mute=None):
		"""
		Adjust the volume of a given application stream in pulseaudio

		WARNING: Not thread safe! This is really intended to be
		instantiated, called once, then thrown away (treat it like a
		function - it's only a class because it needs some internal
		state passed to and from the various callbacks)
		"""

		# Is there a way to do these with decorators?
		# The problem is that transforming these into pa_... types can
		# only occur when the class is instantiated (and the functions
		# transformed into instance methods hiding the self parameter
		# from pa_...), but not when the functions are initially
		# defined (they are still ordinary functions at that point).
		#
		# Basically, I'd need a decorator that does not apply to the
		# function following it's definition, but instead automatically
		# applies to the instance method created when the class is
		# instantiated
		self._finished_callback = _lib.pa_context_success_cb_t(self._finished_callback)
		self._finished_ref_callback = _lib.pa_context_success_cb_t(self._finished_ref_callback)
		self._sink_input_info_callback = _lib.pa_sink_input_info_cb_t(self._sink_input_info_callback)
		self._sink_info_callback = _lib.pa_sink_info_cb_t(self._sink_info_callback)
		self._context_state_callback = _lib.pa_context_notify_cb_t(self._context_state_callback)

		# Only 1 command allowed simultaneously for now
		assert(int(vol_delta is not None) + int(toggle_mute) + int(mute is not None) == 1)

		self.app_name = app_name
		self.vol_delta = vol_delta
		self.toggle_mute = toggle_mute
		self.mute = mute

		self.ret_vol = None
		self.ret_mute = None

		self.eof = None
		self.count = 0

		self._main()

		return (self.ret_vol, self.ret_mute)

	#@_lib.pa_context_success_cb_t - see note above
	def _finished_callback(self, context, success, userdata):
		# print "Success: %i" % success
		_lib.pa_mainloop_quit(self._mainloop, 0)

	#@_lib.pa_context_success_cb_t - see note above
	def _finished_ref_callback(self, context, success, userdata):
		# print "Success: %i" % success
		self.count -= 1
		if not self.count and self.eof:
			_lib.pa_mainloop_quit(self._mainloop, 0)

	def _input_vol(self, context, sink_input_info):
		vol = sink_input_info.volume

		self.ret_vol += self.vol_delta
		_lib.pa_cvolume_set(vol, vol.channels, _lib.pa_sw_volume_from_linear(self.ret_vol))

		op = _lib.pa_context_set_sink_input_volume(context, sink_input_info.index, vol, self._finished_callback, None)
		_lib.pa_operation_unref(op)

	def _output_vol(self, context, sink_info):
		vol = sink_info.volume

		self.ret_vol += self.vol_delta
		_lib.pa_cvolume_set(vol, vol.channels, _lib.pa_sw_volume_from_linear(self.ret_vol))

		op = _lib.pa_context_set_sink_volume_by_index(context, sink_info.index, vol, self._finished_ref_callback, None)
		_lib.pa_operation_unref(op)

	def _input_mute(self, context, sink_input_info, mute):
		self.ret_mute = mute
		op = _lib.pa_context_set_sink_input_mute(context, sink_input_info.index, mute, self._finished_callback, None)
		_lib.pa_operation_unref(op)

	def _output_mute(self, context, sink_info, mute):
		self.ret_mute = mute
		op = _lib.pa_context_set_sink_mute_by_index(context, sink_info.index, mute, self._finished_ref_callback, None)
		_lib.pa_operation_unref(op)

	def _input_toggle_mute(self, context, sink_input_info):
		self._input_mute(context, sink_input_info, int(not sink_input_info.mute))

	def _output_toggle_mute(self, context, sink_info):
		self._output_mute(context, sink_info, int(not sink_info.mute))

	#@_lib.pa_sink_input_info_cb_t - see note above
	def _sink_input_info_callback(self, context, info, eol, userdata):
		if eol: return
		# print 'SINK IN', info.contents.name
		if info.contents.name == self.app_name:
			self.ret_vol = _lib.pa_sw_volume_to_linear(
					_lib.pa_cvolume_avg(info.contents.volume))
			self.ret_mute = info.contents.mute
			if self.vol_delta is not None:
				self._input_vol(context, info.contents)
			if self.toggle_mute:
				self._input_toggle_mute(context, info.contents)
			if self.mute is not None:
				self._input_mute(context, info.contents, int(self.mute))

	#@_lib.pa_sink_info_cb_t - see note above
	def _sink_info_callback(self, context, info, eol, userdata):
		# I may be able to avoid the need to enumerate these since I'm
		# applying the volume change to every output. I just need to know
		# the total number of outputs, right? Assuming index is 0 through N
		if eol:
			self.eof = True
			if not self.count:
				_lib.pa_mainloop_quit(self._mainloop, 0)
			return
		self.count += 1
		self.ret_vol = _lib.pa_sw_volume_to_linear(
				_lib.pa_cvolume_avg(info.contents.volume))
		self.ret_mute = info.contents.mute
		if self.vol_delta is not None:
			self._output_vol(context, info.contents)
		if self.toggle_mute:
			self._output_toggle_mute(context, info.contents)
		if self.mute is not None:
			self._output_mute(context, info.contents, int(self.mute))

	#@_lib.pa_context_notify_cb_t - see note above
	def _context_state_callback(self, context, userdata):
		state = _lib.pa_context_get_state(context)
		# print 'Context state change: %i' % (state)
		if state == _lib.PA_CONTEXT_READY:
			if self.app_name:
				op = _lib.pa_context_get_sink_input_info_list(context, self._sink_input_info_callback, None)
			else:
				op = _lib.pa_context_get_sink_info_list(context, self._sink_info_callback, None)
			_lib.pa_operation_unref(op)

	def _main(self):
		self._mainloop = _lib.pa_mainloop_new()
		mainloop_api = _lib.pa_mainloop_get_api(self._mainloop)
		context = _lib.pa_context_new(mainloop_api, "i3companion") # Alt: _with_proplist
		_lib.pa_context_set_state_callback(context, self._context_state_callback, None)
		_lib.pa_context_connect(context, None, _lib.PA_CONTEXT_NOAUTOSPAWN, None)

		_lib.pa_mainloop_run(self._mainloop, None)

		# raw_input('Enter to close\n')

		_lib.pa_context_disconnect(context)
		_lib.pa_context_unref(context)
		# _lib.pa_mainloop_threaded_stop(self._mainloop)
		_lib.pa_mainloop_free(self._mainloop)


if __name__ == '__main__':
	print PulseAppVolume()(None, -0.05)
	# print PulseAppVolume()(None, toggle_mute=True)
	#print PulseAppVolume()('Spotify', -0.05)
	#print PulseAppVolume()('Spotify', toggle_mute=True)
	#print PulseAppVolume()('Spotify', mute=False)
	#print PulseAppVolume()('Spotify', 0.05, toggle_mute=True)
