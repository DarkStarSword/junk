#!/usr/bin/env python

import functools

def notify(msg, key=None, **kwargs):
	print msg

def notify_exception(arg):
	"""
	Decorator to catch unhandled exceptions and display some info.
	Exceptions are re-raised to allow normal exception handling to occur.
	"""
	comment = None
	def wrap1(f):
		@functools.wraps(f)
		def wrap2(*args, **kwargs):
			try: return f(*args, **kwargs)
			except Exception, e:
				if hasattr(e, 'notified') and e.notified == True:
					raise # Already notified, just pass back up the stack
				if comment:
					notify('%s %s: %s' % (e.__class__.__name__, comment, e))
				else:
					notify('%s: %s' % (e.__class__.__name__, e))
				e.notified = True # Prevent further notify_exception wrappers from notifying this again
				#raise e # If we have the interpreter up, this will still allow it to print the whole back trace
				raise
		return wrap2
	if isinstance(arg, str):
		comment = arg
		return wrap1
	# No comment was passed in, so we need one less level of indirection
	# (arg is what we are decorating)
	return wrap1(arg)

def async(func):
	@functools.wraps(func)
	def wrap(*args, **kwargs):
		import threading
		return threading.Thread(target=func, args=args, kwargs=kwargs).start()
	return wrap
