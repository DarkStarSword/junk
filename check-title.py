#!/usr/bin/env python

import re

# I've done this before...
dont_capitalise = [(re.compile(r'(?<!\w)%s(?!\w)' % re.escape(word.title())), word) for word in \
	['and', 'but', 'or', 'nor', 'to', 'over', 'an', 'a', 'the', 'for',
	'yet', 'so', 'because', 'if', 'so that', 'after', 'when', 'although',
	'while', 'even though', 'of', 'in', 'on', 'with', 'as', 'by', 'at',
	'from', 'vs.']]

def first_middle_last(title):
	first = title.strip()
	try:
		(first, last) = first.split(' ', 1)
	except ValueError:
		last = ''
	try:
		(middle, last) = last.rsplit(' ', 1)
	except ValueError:
		middle = ''
	return (first, middle, last)

def rejoin_title(first, middle, last):
	return ' '.join(filter(None, [first, middle, last]))

def _better_title(title, title_func):
	(first, middle, last) = map(title_func, first_middle_last(title))
	for (exp, word) in dont_capitalise:
		middle = exp.sub(word, middle)
	return rejoin_title(first, middle, last)

def better_title_nolower(title):
	'''
	Like str.title, but doesn't capitalise certain words and doesn't change
	letters that are already capitals to lower case.
	'''
	def title_nolower(title):
		if not title:
			return title
		return ' '.join([ word[0].upper() + word[1:] for word in title.split(' ') ])
	return _better_title(title, title_nolower)

def better_title(title):
	'''
	Like str.title, but doesn't capitalise certain words.
	'''
	return _better_title(title, str.title)

def main():
	import sys
	print better_title(' '.join(sys.argv[1:]))
	# print better_title_nolower(' '.join(sys.argv[1:]))

if __name__ == '__main__':
	main()
