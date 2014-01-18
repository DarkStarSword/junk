#!/usr/bin/env python

import sys
import struct
from StringIO import StringIO

def pr_unknown(data, print_unknown):
	if print_unknown:
		decoded = struct.unpack('%dB' % len(data), data)
		print>>sys.stderr, '[? ' + ' '.join([ '%.2X' % x for x in decoded ]) + ' ?]'

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

class DepotChunk(object):
	def __init__(self, sha):
		self.sha = sha
	def __str__(self):
		return '%.10i:%.10i  %s (%#.8x %i)' % (self.off, self.off+self.len, self.sha, self.unk1, self.unk2)
	def __cmp__(self, other):
		return cmp(self.off, other.off)

class DepotHash(list):
	def __str__(self):
		return '\n\t\t'.join(map(str, ['           %10i  %s (%s)' % (self.filesize, self.sha, self.filetype)] + sorted(self)))

def dump_hash(f, filename):
	return f.read().encode('hex')

def decode_hash(f, filename):
	import hashlib

	# It looks like there are bytes describing the data that follows, so
	# it's possible that the order may not need to be as strict as this.
	# If an assert fails in the future I may need to refactor this to allow
	# for more flexible ordering (or another edge case has been found).

	ret = DepotHash()

	assert(f.read(1) == '\x10')

	ret.filesize = decode_compressed_int(f)

	assert(f.read(1) == '\x18')

	filetype = {
		'\x00': 'file',
		'\x01': 'config file',
		'\x02': 'unidentified file type 0x02 (gam?)',
		'\x04': 'unidentified file type 0x04 (vpk?)',
		'\x08': 'unidentified file type 0x08', # Hydrophobia: Prophecy seems to have this flag set for lots of files
		'\x20': 'unidentified file type 0x20 (setup?)', # The Ship uses this for DXSETUP.exe
		'\x40': 'directory',
		'\x80': 'post install script',
		'\xa0': 'post install executable (?)', # Serious Sam 3 uses this for Sam3.exe and Sam3_Unrestricted.exe
	}[f.read(1)]

	if filetype == 'directory':
		assert(ret.filesize == 0)
	elif filetype.startswith('post install'):
		filetype += ' flags: %s' % f.read(1).encode('hex')

	ret.filetype = filetype

	assert(f.read(2) == '\x22\x14') # 0x22 = name hash, 0x14 = sizeof(sha1)

	# sha1 of the filename in lower case using \ as a path separator
	name_hash = f.read(20)# .encode('hex')
	assert(hashlib.sha1(filename.lower()).digest() == name_hash)

	assert(f.read(2) == '\x2a\x14') # 0x2a = full hash, 0x14 = sizeof(sha1)

	# For directories and empty files this is just all 0s, for non-empty
	# files this is a sha1 of the whole file:
	ret.sha = f.read(20).encode('hex')

	while True:
		t = f.read(1)
		if t == '':
			break
		assert(t == '\x32')
		chunk_len = decode_compressed_int(f)
		chunk = StringIO(f.read(chunk_len))
		assert(chunk.read(2) == '\x0a\x14') # 0x0a = chunk hash, 0x14 = sizeof(sha1)

		chunk_sha = chunk.read(20).encode('hex')

		chunk_meta = DepotChunk(chunk_sha)
		while True:
			type = chunk.read(1)
			if type == '':
				break
			type = {
				'\x18': 'off',
				'\x20': 'len',

				# Seems to be an identifier - chunks sharing
				# sha1s have matching unk1 fields, even between
				# different files (at least within a deopt):
				'\x15': 'unk1',

				# Whereas this can be repeated on differing
				# chunks. Appears to usually be of a similar
				# value to the len field, but not (ever?)
				# exact - can be greater or smaller.
				# Sometimes much smaller:
				'\x28': 'unk2',

				}[type] # .get(type, 'UNKNOWN TYPE %s' % type.encode('hex'))

			if type == 'unk1':
				# FIXME: Format string is a guess, I don't know
				# what this field is, nor what endian it is in.
				# It doesn't seem to be encoded the same way
				# other integers are in these files.
				(val,) = struct.unpack('<I', chunk.read(4))
			else:
				val = decode_compressed_int(chunk)

			setattr(chunk_meta, type, val)

		ret.append(chunk_meta)
	return ret

def decode_entry(f):
	total_len = decode_compressed_int(f)
	data = StringIO(f.read(total_len))
	filename = _decode_entry(data)
	try:
		h = decode_hash(data, filename)
		# h = dump_hash(data, filename)
	except:
		h = 'ERROR DECODING HASH'
		raise
	return (filename, h)

def dump_remaining_data(f):
	print>>sys.stderr, 'Remaining undecoded data:'
	try:
		while True:
			for i in range(2):
				for j in range(8):
					print>>sys.stderr, '%.2X' % struct.unpack('B', f.read(1))[0],
				print>>sys.stderr, '',
			print>>sys.stderr
	except:
		print>>sys.stderr
		return

def _decode_depotcache(filename, print_unknown = False):
	with file(filename, 'r') as f:
		pr_unexpected(f.read(4), 'D017F671', "Unexpected magic value: ")
		pr_unknown(f.read(3), print_unknown)
		pr_unexpected(f.read(1), '00')
		while True:
			byte = struct.unpack('B', f.read(1))[0]
			if byte == 0x0a:
				yield decode_entry(f)
			elif byte == 0xbe:
				if print_unknown:
					print>>sys.stderr, '0xBE FOUND, ENDING'
					dump_remaining_data(f)
				return
			else:
				print 'WARNING: UNKNOWN TYPE 0x%.2X' % byte

def decode_depotcache(filename, print_unknown = False):
	for (filename, h) in _decode_depotcache(filename, print_unknown):
		yield filename

def main():
	for filename in sys.argv[1:]:
		print>>sys.stderr, 'Decoding %s...' % filename
		for entry in _decode_depotcache(filename, True):
			print '%s\n\t\t%s' % entry
		print>>sys.stderr

if __name__ == '__main__':
	main()
