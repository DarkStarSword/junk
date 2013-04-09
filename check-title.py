#!/usr/bin/env python

import re

# I've done this before...
dont_capitalise = [(re.compile(r'(?<!\w)%s(?!\w)' % re.escape(word.title())), word) for word in \
	['and', 'but', 'or', 'nor', 'to', 'over', 'an', 'a', 'the', 'for',
	'yet', 'so', 'because', 'if', 'so that', 'after', 'when', 'although',
	'while', 'even though', 'of', 'in', 'on', 'with', 'as', 'by', 'at',
	'from', 'vs.']]

def better_title_nolower(title):
	'''
	Like str.title, but doesn't capitalise certain words and doesn't change
	letters that are already capitals to lower case.
	'''
	tmp = title.split(' ')
	for (i, word) in enumerate(tmp):
		tmp[i] = word[0].upper() + word[1:]
	tmp = ' '.join(tmp)
	for (exp, word) in dont_capitalise:
		tmp = exp.sub(word, tmp)
	return tmp

def better_title(title):
	'''
	Like str.title, but doesn't capitalise certain words.
	'''
	tmp = title.title()
	for (exp, word) in dont_capitalise:
		tmp = exp.sub(word, tmp)
	return tmp

def main():
	import sys
	print better_title(' '.join(sys.argv[1:]))

if __name__ == '__main__':
	main()
