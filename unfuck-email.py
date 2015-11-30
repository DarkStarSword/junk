#!/usr/bin/env python3

import sys, os

def unfuck(s):
    s = s.replace('=\n', '')
    for c in range(ord(' '), ord('~')):
        s = s.replace('=%.2X' % c, chr(c))
    return s

def main():
    for file in sys.argv[1:]:
        print(unfuck(open(file, 'r').read()))

if __name__ == '__main__':
    main()
