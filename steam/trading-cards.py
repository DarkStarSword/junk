#!/usr/bin/env python

# Inspired by a Google Drive spreadsheet by Han Lin Yap (http://yap.nu/)

# The spreadsheet no longer works, was awkward to use & I can't find the
# original link, so I ported the concept over to Python. The only actual
# "copied" code from the original is the Steam URLs, everything else was
# written from scratch.

# Why? The badges page does not show owned games with cards if all the card
# drops have been obtained & traded away and the game has not been played in
# the last two weeks.

import sys

# %i will be replaced by the page number
card_search_url = 'http://store.steampowered.com/search/?sort_by=Name&sort_order=ASC&category1=998&category2=29&page=%i'
card_search_cache = '.trading-cards-cache-page-%i'
cache_timeout = 60 * 60 # 1 Hour

# First %s replaced with "profiles" if profile ID is numeric, otherwise "ids"
# for vanity URLs. Second %s is replaced with profile ID.
profile_games_url = 'http://steamcommunity.com/%s/%s/games?tab=all&xml=1'
profile_games_cache = '.trading-cards-games-cache-%s-%s'

def geturl_cached(url, cache):
	import urllib2, os, time

	if os.path.isfile(cache):
		age = time.time() - os.stat(cache).st_mtime
		if age >= 0 and age < cache_timeout:
			print>>sys.stderr, 'Using cache %s' % cache
			return open(cache)
		print>>sys.stderr, 'Cache too old, refetching.'
	print>>sys.stderr, 'Fetching URL %s...' % url
	request = urllib2.urlopen(url)
	content = request.read()
	open(cache, 'w').write(content)
	return open(cache)

def steam_search_card_apps():
	from HTMLParser import HTMLParser
	class SteamSearchResultParser(HTMLParser):
		import re

		appID_url = re.compile(r'http://store\.steampowered\.com/app/(?P<appID>\d+)/');
		a_class = 'search_result_row'
		pagination_onclick = 'SearchLinkClick('

		def __init__(self):
			HTMLParser.__init__(self)
			self.apps = {}
			self.in_pagination = self.in_app_title = False
			self.in_appID = None
			self.pages = 1

		def handle_a(self, attrs):
			if 'class' in attrs and attrs['class'].startswith(self.a_class):
				match = self.appID_url.match(attrs['href'])
				if match:
					self.in_appID = int(match.group('appID'))
			if 'onclick' in attrs and attrs['onclick'].startswith(self.pagination_onclick):
				self.in_pagination = True

		def handle_starttag(self, tag, attrs):
			attrs = dict(attrs)
			if tag == 'a' and 'href' in attrs:
				return self.handle_a(attrs)
			if tag == 'h4' and self.in_appID is not None:
				self.in_app_title = True

		def handle_endtag(self, tag):
			self.in_pagination = self.in_app_title = False
			if tag == 'a':
				self.in_appID = None

		def handle_data(self, data):
			if self.in_pagination:
				self.pages = max(self.pages, int(data))
			if self.in_app_title:
				self.apps[self.in_appID] = data.strip()

	parser = SteamSearchResultParser()
	page = 1
	print>>sys.stderr, 'Processing page %i...' % page
	while page <= parser.pages:
		if parser.pages > 1:
			print>>sys.stderr, 'Processing page %i/%i...' % (page, parser.pages)
		parser.feed(geturl_cached(card_search_url % page, card_search_cache % page).read())
		page += 1
	return parser.apps

def steam_profile_games(profile):
	try:
		from defusedxml import minidom
	except ImportError:
		print>>sys.stderr, 'WARNING: pyhon-defusedxml not available, falling back to unsafe standard libraries...'
		from xml.dom import minidom

	sub = ('id', profile)
	if profile.isdigit():
		sub = ('profiles', profile)
	xml = minidom.parse(geturl_cached(profile_games_url % sub, profile_games_cache % sub))

	return [ int(game.getElementsByTagName('appID')[0].firstChild.data) \
			for game in xml.getElementsByTagName('game') ]

def print_apps(apps, games):
	print " appID | Own | Title"
	print "-------+-----+------"
	for (id, app) in sorted(apps.items(), cmp=lambda x,y: cmp(x[1], y[1])):
		owned = {True: 'Y', False: ' '}[id in games]
		print "%6i |  %s  | %s" % (id, owned, app)

def main():
	steam_profile = sys.argv[1]

	card_apps = steam_search_card_apps()
	profile_games = steam_profile_games(steam_profile)

	games = filter(lambda appID: appID in card_apps, profile_games)

	print_apps(card_apps, games)

	print
	print '%i Games with Trading Cards Owned' % len(games)

if __name__ == '__main__':
	main()
