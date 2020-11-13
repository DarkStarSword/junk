#!/usr/bin/env python

import json, sys

def main():
    nargs = len(sys.argv)
    if nargs == 1:
        f = sys.stdin
    elif nargs == 2:
        f = open(sys.argv[1], 'r')
    else:
        print('Usage: %s file' % sys.argv[0])
        return
    json.dump(json.load(f), sys.stdout, indent=2)

if __name__ == '__main__':
    main()
