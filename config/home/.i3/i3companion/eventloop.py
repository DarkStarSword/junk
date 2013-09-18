#!/usr/bin/env python

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
		method(*args, **kwargs)

	def poll(self, timeout=-1, maxevents=-1):
		return self._epoll.poll(timeout, maxevents)

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
