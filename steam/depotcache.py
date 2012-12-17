#!/usr/bin/env python

import sys
import struct
from StringIO import StringIO

print_unknown = True

def pr_unknown(data):
	if print_unknown:
		decoded = struct.unpack('%dB' % len(data), data)
		print '[? ' + ' '.join([ '%.2X' % x for x in decoded ]) + ' ?]'

def pr_unexpected(data, expected, note=''):
	l = len(data)
	expected_bytes = [ int(expected[i:i+2], 16) for i in range(0, l*2, 2) ]
	decoded = struct.unpack('%dB' % len(data), data)
	if decoded != tuple(expected_bytes):
		print 'WARNING: %sExpected [%s], got [%s]' % (note, \
				' '.join([ '%.2X' % x for x in expected_bytes ]), \
				' '.join([ '%.2X' % x for x in decoded ]))
		return 1
	return 0

def decode_compressed_int(f):
	val = bytes = 0
	while True:
		byte = struct.unpack('B', f.read(1))[0]
		val |= (byte & 0x7f) << (bytes * 7)
		bytes += 1
		if (byte & 0x80) == 0:
			return val

def _decode_entry(f):
	pr_unexpected(f.read(1), '0A')
	filename_len = decode_compressed_int(f)
	return f.read(filename_len)

def decode_entry(f):
	total_len = decode_compressed_int(f)
	data = f.read(total_len)
	return _decode_entry(StringIO(data))

def dump_remaining_data(f):
	print 'Remaining undecoded data:'
	try:
		while True:
			for i in range(2):
				for j in range(8):
					print '%.2X' % struct.unpack('B', f.read(1))[0],
				print '',
			print
	except:
		print
		return

def decode_depotcache(filename):
	with file(filename, 'r') as f:
		pr_unexpected(f.read(4), 'D017F671', "Unexpected magic value: ")
		pr_unknown(f.read(3))
		pr_unexpected(f.read(1), '00')
		while True:
			byte = struct.unpack('B', f.read(1))[0]
			if byte == 0x0a:
				print decode_entry(f)
			elif byte == 0xbe:
				print '0xBE FOUND, ENDING'
				if print_unknown:
					dump_remaining_data(f)
				return
			else:
				print 'WARNING: UNKNOWN TYPE 0x%.2X' % byte


def main():
	for filename in sys.argv[1:]:
		print 'Decoding %s...' % filename
		decode_depotcache(filename)
		print

if __name__ == '__main__':
	main()
