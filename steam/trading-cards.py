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

cache_timeout = 3 * 60 * 60 # 3 Hours

# %i will be replaced by the page number
card_search_url = 'http://store.steampowered.com/search/?sort_by=Name&sort_order=ASC&&category2=29&page=%i'
card_search_cache = '.trading-cards-cache-page-%i'

# First %s replaced with "profiles" if profile ID is numeric, otherwise "ids"
# for vanity URLs. Second %s is replaced with profile ID.
profile_games_url = 'http://steamcommunity.com/%s/%s/games?tab=all&xml=1'
profile_games_cache = '.trading-cards-games-cache-%s-%s'

# http://wiki.teamfortress.com/wiki/User:RJackson/StorefrontAPI
# %s replaced with comma separated list of appIDs to query
appid_url = 'http://store.steampowered.com/api/appdetails/?appids=%s&filters=basic,categories'
# %s replaced with hash of all requested appIDs
appid_cache = '.trading-cards-appID-cache-%s'
appids_per_request = 25

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

def _steam_appdetails(appIDs):
	import hashlib

	sub = ','.join(map(str, appIDs))
	hash = hashlib.sha1(sub).hexdigest()
	return geturl_cached(appid_url % sub, appid_cache % hash)

def steam_appdetails(appIDs):
	import json
	ret = {}
	while len(appIDs):
		request = appIDs[:appids_per_request]
		appIDs = appIDs[appids_per_request:]
		content = _steam_appdetails(request)
		ret.update(json.loads(content.read()))
	return ret

def filter_steam_appdetails_trading_cards(appIDs):
	ret = []
	info = steam_appdetails(appIDs)
	for appID in info:
		try:
			for category in info[appID]['data']['categories']:
				if category['description'] == 'Steam Trading Cards':
					print>>sys.stderr, '%s (%s) has trading cards, fullgame = %s (%s)' % \
							(appID, info[appID]['data']['name'], \
							info[appID]['data']['fullgame']['appid'], \
							info[appID]['data']['fullgame']['name'])
					ret.append(int(info[appID]['data']['fullgame']['appid']))
		except KeyError, e:
			if str(e) not in ["'data'", "'categories'"]:
				print>>sys.stderr, 'Skipping %s - appdetails has no %s' % (appID, str(e))
			continue
	return ret

def print_apps(apps, games, demos):
	print "  appID  | Own | Title"
	print "---------+-----+------"
	for (id, app) in sorted(apps.items(), cmp=lambda x,y: cmp(x[1], y[1])):
		owned = ' '
		if id in games:
			owned = 'Y'
		elif id in demos:
			owned = 'D'
		print "%8i |  %s  | %s" % (id, owned, app)

def main():
	steam_profile = sys.argv[1]

	card_apps = steam_search_card_apps()
	profile_games = steam_profile_games(steam_profile)

	games = filter(lambda appID: appID in card_apps, profile_games)
	unmatched = filter(lambda appID: appID not in card_apps, profile_games)
	demos = []

	print>>sys.stderr, '%i/%i games matched store trading card query' % (len(games), len(profile_games))

	if unmatched:
		print>>sys.stderr, 'Fetching details for remaining %i games...' % len(unmatched)
		demos = filter_steam_appdetails_trading_cards(unmatched)

	print_apps(card_apps, games, demos)

	print
	print '%i Games with Trading Cards Owned' % len(games)

if __name__ == '__main__':
	main()
