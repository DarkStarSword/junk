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
    j = json.dumps(json.load(f), indent=2)
    print('\n'.join(map(str.rstrip, j.splitlines())))

if __name__ == '__main__':
    main()
