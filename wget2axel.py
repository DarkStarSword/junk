#!/usr/bin/env python

def url_size(url):
	import httplib, urllib2
	proto, url = urllib2.splittype(url)
	assert(proto.lower() == 'http')
	host, path = urllib2.splithost(url)
	# http://stackoverflow.com/questions/107405/how-do-you-send-a-head-http-request-in-python
	conn = httplib.HTTPConnection(host)
	conn.request('HEAD', path)
	res = conn.getresponse()
	# FIXME: Follow any redirects
	return int(res.getheader('content-length'))

def axel_divide(size, num_connections):
	chunk_size = size // num_connections
	ret = [[0, chunk_size - 1]]
	for i in range(1, num_connections):
		start_byte = ret[i-1][1] + 1
		ret.append([start_byte, start_byte + chunk_size])
	ret[-1][1] = size - 1
	print ret
	return ret

def adjust_connection_current_bytes(filesize, connections):
	for (i, (start_byte, end_byte)) in enumerate(connections):
		if start_byte < filesize:
			connections[i][0] = filesize
	print connections
	return connections

def save_axel_state(state_filename, filesize, connections):
	import struct
	f = open(state_filename, 'w')
	f.write(struct.pack('i', len(connections))) # Two separate writes
	f.write(struct.pack('q', filesize))         # to avoid padding
	for (start_byte, end_byte) in connections:
		f.write(struct.pack('q', start_byte))
	f.close()

def pad_file(filename, length):
	f = open(filename, 'w')
	f.truncate(length)
	f.close()

if __name__ == '__main__':
	import sys, os

	url = sys.argv[1]
	filename = sys.argv[2]
	state_filename = '%s.st' % filename
	if os.path.exists(state_filename):
		print 'Axel state file already exists - aborting!'
		sys.exit(1)

	length = url_size(url)
	filesize = os.stat(filename).st_size
	print '%i / %i (%i bytes to go)' % (filesize, length, length - filesize)
	assert(filesize < length)

	target_connections = 4
	num_connections = length // ((length - filesize) // target_connections)
	print 'Telling axel to use %i connections (%.2f are already complete)' % (num_connections, filesize / (float(length) / num_connections))

	connections = axel_divide(length, num_connections)
	connections = adjust_connection_current_bytes(filesize, connections)

	save_axel_state(state_filename, filesize, connections)
	# pad_file(filename, length)
