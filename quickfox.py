#!/usr/bin/env python3

'''
Python script to transmit a file over UDP quickly in the presence of abnormally
high packet loss that would normally kill the speed of any TCP connection.

The Brown Fox was quick, even in the face of obstacles.
'''

# TODO LIST:
# - Send info about the file to receiver ahead of time
#   - Receiver stop once full file received
# - Allow for interrupted transfer to be resumed
# - Add timeouts
# - Other connection modes, like STUN
# - Retry handshake in case of packet loss
# - Binary encode handshake
# - Protection against spoofed packets
# - AES Encryption
#   - Key exchange?
#   - Stateless implications
# - Proxy server mode
#   - Support multiple clients
# - rsync mode
# - Optional zlib
# - Heuristics to adjust speed for congestion that does not fuck up with
#   unrelated packet loss

import sys, os
import argparse
import socket
import struct, json
import time
import collections

peer = None

class HandShake(object):
	packet_type = 0
	signature = b'brownfox'
	version = 1

	def __init__(self, args=None):
		self.negotiated = False

		if args is None:
			return

		if args.in_file:
			self.mode = 'send'
		elif args.out_file:
			self.mode = 'recv'
		else:
			raise ValueError()
		self.rate = args.rate
		self.packet_size = args.packet_size

	def serialise(self):
		# Using a binary version here so we don't get locked into json
		# encoding this packet forever:
		packet = struct.pack('>BB8s', self.packet_type, self.version, self.signature)

		# json encoding the rest for flexibility during development.
		# Might keep this, might not:
		s = {
			'mode': self.mode,
			'rate': self.rate,
			'packet': self.packet_size
		}
		packet += json.dumps(s, ensure_ascii=True).encode('ascii')
		# print(packet)
		return packet

	def deserialise(self, packet):
		if len(packet) < 10:
			raise ValueError('Protocol Mismatch: Short handshake')

		packet_type, version, signature = struct.unpack('>BB8s', packet[:10])
		if packet_type != self.packet_type or version != self.version or signature != self.signature:
			raise ValueError('Protocol Mismatch')

		s = json.loads(packet[10:].decode('ascii'))
		self.mode = s['mode']
		self.rate = s['rate']
		self.packet_size = s['packet']

		if self.mode not in ('send', 'recv'):
			raise ValueError('Protocol Mismatch: Unsupported mode')

		if type(self.rate) != int or type(self.packet_size) != int:
			raise ValueError('Protocol Mismatch: Bad type')

	def negotiate(self, other):
		if self.mode == other.mode:
			raise ValueError('Incompatible transfer modes')
		self.rate = min(self.rate, other.rate)
		self.packet_size = min(self.packet_size, other.packet_size)
		self.negotiated = True

class FileChunk(object):
	packet_type = 1
	overhead = 9

	def __init__(self, fp = None, offset = None, size = None):
		if fp is None:
			return

		self.fp = fp
		self.offset = offset
		self.size = size - self.overhead
		self.sent = 0

	def serialise(self):
		packet = struct.pack('>BQ', self.packet_type, self.offset)
		self.fp.seek(self.offset)
		return packet + self.fp.read(self.size)

	def deserialise(self, packet):
		if len(packet) < self.overhead:
			raise ValueError('Protocol Mismatch: Short data packet')

		packet_type, self.offset = struct.unpack('>BQ', packet[:self.overhead])
		if packet_type != self.packet_type:
			raise ValueError('Wrong packet type')

		self.data = packet[self.overhead:]
		self.size = len(self.data)

	def write(self, fp):
		self.fp = fp
		fp.seek(self.offset)
		fp.write(self.data)


class Ack(object):
	packet_type = 2
	overhead = 2

	def __init__(self, offsets=None):
		self.offsets = offsets

	def serialise(self):
		# TODO: Ack several recent packets to reduce resends in case an ack gets lost
		packet = struct.pack('>BB', self.packet_type, len(self.offsets))
		for offset in self.offsets:
			packet += struct.pack('>Q', offset)
		# print(packet)
		return packet

	def deserialise(self, packet):
		if len(packet) < self.overhead:
			raise ValueError('Protocol Mismatch: Short ACK packet')

		packet_type, num_offsets = struct.unpack('>BB', packet[:self.overhead])
		self.offsets = []
		for i in range(num_offsets):
			off = self.overhead + (i * 8)
			self.offsets.append(struct.unpack('>Q', packet[off:off+8])[0])
		if packet_type != self.packet_type:
			raise ValueError('Wrong packet type')

def decode_packet(packet):
	if len(packet) < 1:
		raise ValueError('Invalid packet')
	p = {
			0: HandShake,
			1: FileChunk,
			2: Ack,
	}[packet[0]]()

	p.deserialise(packet)

	return p


def start_server(args):
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind((args.listen, args.port))

	handshake = HandShake(args)

	while True:
		data, address = sock.recvfrom(4096)
		try:
			client_handshake = HandShake()
			client_handshake.deserialise(data)
			handshake.negotiate(client_handshake)
		except Exception as e:
			print('%s: %s' % (e.__class__.__name__, str(e)))
			continue
		peer = address
		break
	print('Accepted connection from %s:%i' % peer)

	sock.sendto(handshake.serialise(), peer)

	return sock, peer, handshake

def start_client(args):
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	peer = socket.gethostbyname(args.server), args.port

	handshake = HandShake(args)

	# TODO: Retry handshake if no response received at all
	sock.sendto(handshake.serialise(), peer)

	# We don't wait for the server handshake here. Since we are expecting
	# packets to be dropped or arrive out of order we need to handle the
	# case where this happens to the handshake from the server, so just
	# move that out to the main transfer loop

	return sock, peer, handshake

def establish_connection(args):
	if args.listen:
		return start_server(args)
	if args.server:
		return start_client(args)

def pr_bytes(rate):
	if rate < 1024:
		return str(rate)
	rate /= 1024
	if rate < 1024:
		return '%iK' % rate
	rate /= 1024
	if rate < 1024:
		return '%iM' % rate
	rate /= 1024
	return '%iG' % rate


def send_loop(sock, peer, handshake, args):
	if not handshake.negotiated:
		# FIXME: Client sending a file will always hit this case
		print('FIXME: handshake negotiation not complete - not starting transfer')
		return

	pps = handshake.rate / handshake.packet_size
	delay = 1 / pps
	print('Packets per second: %f' % pps)
	print('Packet interval: %f' % delay)

	# FIXME: Open this earlier to avoid late errors
	fp = open(args.in_file, 'rb')
	filesize = os.fstat(fp.fileno()).st_size
	pos = 0
	in_flight_chunks = collections.OrderedDict()
	last_time_printed = time.time()
	last_total_sent = total_sent = unique_sent = resends = resends_size = chunks = 0

	while True:
		sock.settimeout(None)

		if len(in_flight_chunks) and (len(in_flight_chunks) > 100 or pos >= filesize):
			# Resend the oldest chunk and move it to the end of the
			# in flight list:
			chunk = in_flight_chunks.popitem(False)[1]
			in_flight_chunks[chunk.offset] = chunk
			resends += 1
			resends_size += chunk.size
		elif pos < filesize:
			chunk = FileChunk(fp, pos, handshake.packet_size)
			in_flight_chunks[pos] = chunk
			pos += chunk.size # Do not use handshake.packet_size - overhead
			chunks += 1
			unique_sent += chunk.size
		else:
			# Should send filesize ahead of time - receiver could miss this packet:
			sock.sendto(Ack([]).serialise(), peer)
			print('Transfer complete and acknowledged')
			break

		total_sent += chunk.size

		sock.sendto(chunk.serialise(), peer)

		cur_time = time.time()
		if cur_time - last_time_printed > 1:
			print('Sent: %s/%s %i%% (%i chunks, %i resends totalling %s, %i not acknowledged) @ %s/s' % \
					(pr_bytes(unique_sent), pr_bytes(filesize), unique_sent/filesize*100,
						chunks, resends, pr_bytes(resends_size), len(in_flight_chunks),
						pr_bytes((total_sent - last_total_sent) / (cur_time - last_time_printed))))
			last_total_sent = total_sent
			last_time_printed = cur_time

		delta = 0
		while True:
			delta = time.time() - cur_time

			sock.settimeout(max(0, delay - delta))
			try:
				data, address = sock.recvfrom(handshake.packet_size)
			except (socket.timeout, BlockingIOError):
				break

			if address != peer:
				continue

			try:
				packet = decode_packet(data)
			except Exception as e:
				print('%s: %s' % (e.__class__.__name__, str(e)))
				continue

			if isinstance(packet, Ack):
				for offset in packet.offsets:
					if offset in in_flight_chunks:
						del in_flight_chunks[offset]

def recv_loop(sock, peer, handshake, args):
	# TODO: Allow partial transfers to be resumed using e.g. a tree hash,
	# rsync like algorithm, or just a state file
	fp = open(args.out_file, 'wb')

	complete_chunks = set()
	last_time = time.time()
	last_total_received = total_received = unique_received = duplicates = chunks = 0
	recent_offsets = []
	while True:
		data, address = sock.recvfrom(handshake.packet_size)
		if address != peer:
			continue

		try:
			packet = decode_packet(data)
		except Exception as e:
			print('%s: %s' % (e.__class__.__name__, str(e)))
			raise
			continue

		if isinstance(packet, HandShake):
			handshake.negotiate(packet)

		if isinstance(packet, FileChunk):
			packet.write(fp)

			if len(recent_offsets) > 15:
				recent_offsets.pop(0)
			recent_offsets.append(packet.offset)

			ack = Ack(recent_offsets)
			sock.sendto(ack.serialise(), peer)

			total_received += packet.size
			if packet.offset in complete_chunks:
				duplicates += 1
			else:
				unique_received += packet.size
				chunks += 1
				complete_chunks.add(packet.offset)

			cur_time = time.time()
			if cur_time - last_time > 1:
				print('Received: %s (%i chunks, %i duplicates) @ %s/s' % \
						(pr_bytes(unique_received), chunks, duplicates,
							pr_bytes((total_received - last_total_received) / (cur_time - last_time))))
				last_total_received = total_received
				last_time = cur_time

		if isinstance(packet, Ack):
			print('Transfer Complete')
			return

def begin_transfer(s, args):
	sock, peer, handshake = s
	if args.in_file:
		return send_loop(sock, peer, handshake, args)
	if args.out_file:
		return recv_loop(sock, peer, handshake, args)

def parse_rate(val):
	if val.isdigit():
		return int(val)
	if len(val) < 2 or not val[:-1].isdigit() or val[-1] not in 'KMkm':
		raise argparse.ArgumentTypeError('%r is not a valid rate')
	return int(val[:-1]) * {
			'K': 1024,
			'M': 1024**2,
			'k': 125,
			'm': 125000,
	}[val[-1]]

def parse_args():
	parser = argparse.ArgumentParser()
	group = parser.add_mutually_exclusive_group(required=True)
	group.add_argument('server', nargs='?',
			help='Connect to another %s listening on the given server' % sys.argv[0])
	group.add_argument('-l', '--listen', nargs='?', const='0.0.0.0',
			help='Listen for incoming connections on this address')

	parser.add_argument('-p', '--port', type=int, default=2063, # Who is geeky enough to get the reference?
			help='Port to use')
	parser.add_argument('-r', '--rate', type=parse_rate, required=True, #default='200K', # TODO: Dynamically adjust rate, just not the way TCP does
			help='Transfer rate to send packets at (optional suffix: K=kilobytes, k=kilobits, M=megabytes, m=megabits)')
	parser.add_argument('-m', '--packet-size', type=int, default=4096,
			help='UDP packet size to use')

	group = parser.add_mutually_exclusive_group(required=True)
	group.add_argument('-i', '--in-file',
			help='File to send')
	group.add_argument('-O', '--out-file',
			help='Where to save retrieved file')

	return parser.parse_args()

def main():
	args = parse_args()

	s = establish_connection(args)
	begin_transfer(s, args)


if __name__ == '__main__':
	main()
