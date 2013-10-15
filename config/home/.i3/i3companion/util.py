#!/usr/bin/env python

def describe_fd(fd):
	import os
	try:
		f = os.readlink('/proc/self/fd/%i' % fd.fileno())
		if os.path.isfile(f):
			return f
	except OSError:
		pass
	return fd.name
