#!/usr/bin/env python

# Recursively rename all files to lower case.
# To test the rename functionality in check_acf.py

import os, sys

def rename_lower(root, fn):
	low = fn.lower()
	if fn != low:
		print os.path.join(root, fn), '==>', os.path.join(root, low)
		os.rename(os.path.join(root, fn), os.path.join(root, low))
	return low

if __name__ == '__main__':
	for path in sys.argv[1:]:
		for (root, dnames, fnames) in os.walk(path):
			for i in range(len(dnames)):
				dnames[i] = rename_lower(root, dnames[i])
			for fn in fnames:
				rename_lower(root, fn)
