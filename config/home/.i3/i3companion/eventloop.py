#!/usr/bin/env python

from pluginmanager import notify
from util import describe_fd

class EventLoop(object):
	import select

	def __init__(self):
		self._fds = {}
		self._epoll = self.select.epoll()
		self.running = True

	def register(self, file, method, args=(), kwargs={}):
		eventmask = self.select.EPOLLIN | self.select.EPOLLPRI
		fd = self.file_fd(file)
		self._fds[fd] = (method, args, kwargs)
		self._epoll.register(fd, eventmask)

	def unregister(self, file):
		fd = self.file_fd(file)
		self._epoll.unregister(fd)
		del self._fds[fd]

	def dispatch(self, fd, eventmask):
		(method, args, kwargs) = self._fds[fd]
		try:
			method(*args, **kwargs)
		except Exception as e:
			import sys, traceback
			traceback.print_exc()
			try:
				notify("i3companion: %s: %s in %s.%s(). Refer to %s for backtrace" %
				       (e.__class__.__name__, str(e),
					method.__module__, method.__name__,
					describe_fd(sys.stderr)), timeout=5000)
			except Exception as e:
				print>>sys.stderr, 'i3companion: Additional error while reporting error:'
				traceback.print_exc()

	def poll(self, timeout=-1, maxevents=-1):
		while True:
			try:
				return self._epoll.poll(timeout, maxevents)
			except IOError as e:
				if e.args[0] == 4: # Interrupted system call
					continue
				raise

	def run(self):
		while self.running:
			for event in self.poll():
				self.dispatch(*event)

	def stop(self):
		self.running = False

	@staticmethod
	def file_fd(file):
		if hasattr(file, 'fileno'):
			return file.fileno()
		return file
