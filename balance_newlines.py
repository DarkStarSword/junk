#!/usr/bin/env python

import sys

def main():
    def width(lines):
        return max(map(len, [' '.join(l) for l in lines]))

    lines = [x.split(' ') for x in sys.stdin.read().strip().split('\n')]
    print >>sys.stderr, 'Before - max width:',  width(lines)

    making_progress = True
    while making_progress:
        making_progress = False
        for i, l in enumerate(lines):
            if not len(l):
                continue
            if i > 0:
                ow = width(lines[i-1:i+1])
                lines[i-1].append(l.pop(0))
                nw = width(lines[i-1:i+1])
                if nw < ow:
                    making_progress = True
                    break
                l.insert(0, lines[i-1].pop(-1))
            if i < len(lines) - 1:
                ow = width(lines[i:i+2])
                lines[i+1].insert(0, l.pop(-1))
                nw = width(lines[i:i+2])
                if nw < ow:
                    making_progress = True
                    break
                l.append(lines[i+1].pop(0))

    print >>sys.stderr, 'After - max width:', width(lines)
    for l in lines:
        print ' '.join(l)

if __name__ == '__main__':
    main()
