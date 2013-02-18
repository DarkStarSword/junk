#!/usr/bin/env python
# vi:ts=4:sw=4:noexpandtab

import serial

prefix = '00100'
remote_id = '00000000' # Pressing the new code button increments this 8-bit value by one
arduino = '/dev/ttyACM0'
baud = 115200

def code(remote_id, device, action):
	dev = {
			'all': '000',
			'1': '111',
			'2': '011',
			'3': '001',
			'4': '101',
		}
	act = {
			'on':     '01',
			'off':    '11',
			'bright': '10',
			'dim':    '00',
		}
	code = dev[device] + act[action] + '1'
	# checksum:
	code += str(int(code[0]) ^ int(code[2]) ^ int(code[4]))
	code += str(int(code[1]) ^ int(code[3]) ^ int(code[5]))
	return prefix + remote_id + code

def do_command(command):
	(device, action) = command.split()
	s = serial.Serial(arduino, baud)
	t = 'tx %s\n' % code(remote_id, device, action)
	s.write(t)
	while not s.readline().startswith('Done'):
		pass
	if action in ('dim', 'bright'):
		for i in range(2):
			s.write(t)
			while not s.readline().startswith('Done'):
				pass
	print 'Done'

def main():
	import sys
	if len(sys.argv) > 1:
		command = ' '.join(sys.argv[1:])
		do_command(command)
	else:
		while True:
			command = raw_input()
			do_command(command)

if __name__ == '__main__':
	main()
