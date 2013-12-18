#!/usr/bin/env python

# Inspired by a Google Drive spreadsheet by Han Lin Yap (http://yap.nu/)

# The spreadsheet no longer works, was awkward to use & I can't find the
# original link, so I ported the concept over to Python. The only actual
# "copied" code from the original is the Steam URLs, everything else was
# written from scratch.

# Why? The badges page does not show owned games with cards if all the card
# drops have been obtained & traded away and the game has not been played in
# the last two weeks.

from HTMLParser import HTMLParser
import sys
import re

cache_timeout = 3 * 24 * 60 * 60 # 3 Days

# %i will be replaced by the page number
card_search_url = 'http://store.steampowered.com/search/?sort_by=Name&sort_order=ASC&&category2=29&page=%i'
card_search_cache = '.trading-cards-cache-page-%i'

# First %s replaced with "profiles" if profile ID is numeric, otherwise "ids"
# for vanity URLs. Second %s is replaced with profile ID.
profile_games_url = 'http://steamcommunity.com/%s/%s/games?tab=all&xml=1'
profile_games_cache = '.trading-cards-games-cache-%s-%s'
profile_badges_url = 'http://steamcommunity.com/%s/%s/badges/'
profile_badges_cache = '.trading-cards-badge-cache-%s-%s'

# http://wiki.teamfortress.com/wiki/User:RJackson/StorefrontAPI
# %s replaced with comma separated list of appIDs to query
appid_url = 'http://store.steampowered.com/api/appdetails/?appids=%s&filters=basic,genres'
# %s replaced with hash of all requested appIDs
appid_cache = '.trading-cards-appID-cache-%s-basic,genres'
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
	class SteamSearchResultParser(HTMLParser):
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
				# NOTE: Title may be overridden from appdetails
				self.apps[self.in_appID] = {'title': data.strip()}

	parser = SteamSearchResultParser()
	page = 1
	print>>sys.stderr, 'Processing page %i...' % page
	while page <= parser.pages:
		if parser.pages > 1:
			print>>sys.stderr, 'Processing page %i/%i...' % (page, parser.pages)
		parser.feed(geturl_cached(card_search_url % page, card_search_cache % page).read())
		page += 1
	return parser.apps

def steam_profile_sub(profile):
	if profile.isdigit():
		return ('profiles', profile)
	return ('id', profile)

def steam_profile_games(profile):
	try:
		from defusedxml import minidom
	except ImportError:
		print>>sys.stderr, 'WARNING: pyhon-defusedxml not available, falling back to unsafe standard libraries...'
		from xml.dom import minidom

	sub = steam_profile_sub(profile)
	xml = minidom.parse(geturl_cached(profile_games_url % sub, profile_games_cache % sub))

	return [ int(game.getElementsByTagName('appID')[0].firstChild.data) \
			for game in xml.getElementsByTagName('game') ]

def steam_profile_badges(profile):
	class SteamProfileBadgesParser(HTMLParser):
		badge_url = re.compile(r'http://steamcommunity\.com/id/[^/]+/[^/]+/(?P<appID>\d+)/(?P<foil>\?border=1)?')
		badge_class = 'badge_row '
		badge_title = 'badge_title'
		badge_level = re.compile(r'Level (?P<level>\d+),')

		def __init__(self):
			HTMLParser.__init__(self)
			self.in_badge = 0
			self.apps = {}
			self.in_app = None
			self.in_title = False

		def handle_a(self, attrs):
			match = self.badge_url.match(attrs['href'])
			if match is None:
				return
			appID = int(match.group('appID'))
			if appID not in self.apps:
				self.apps[appID] = {}
			if match.group('foil') is not None:
				self.apps[appID]['foil'] = True
				self.in_badge = 0
				return
			self.in_app = appID

		def handle_div(self, attrs):
			if self.in_badge or ('class' in attrs and attrs['class'].startswith(self.badge_class)):
				self.in_badge += 1
			if 'class' in attrs and attrs['class'] == self.badge_title:
				self.in_title = True

		def handle_starttag(self, tag, attrs):
			attrs = dict(attrs)
			if tag == 'a' and 'href' in attrs:
				return self.handle_a(attrs)
			if tag == 'div':
				return self.handle_div(attrs)

		def handle_endtag(self, tag):
			if self.in_badge and tag == 'div':
				self.in_badge -= 1
			if self.in_badge == 0:
				self.in_app = None
			self.in_title = False

		def handle_data(self, data):
			if not self.in_app:
				return
			if self.in_badge:
				match = self.badge_level.match(data.lstrip())
				if match:
					self.apps[self.in_app]['level'] = int(match.group('level'))
			if self.in_title and 'title' not in self.apps[self.in_app]:
				self.apps[self.in_app]['title'] = data.strip()

	sub = steam_profile_sub(profile)
	parser = SteamProfileBadgesParser()
	parser.feed(geturl_cached(profile_badges_url % sub, profile_badges_cache % sub).read())
	return parser.apps

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
		ret.update(json.loads(_steam_appdetails(request).read()))
	return ret

def classify_steam_apps(apps):
	def trans(type):
		try:    return {'dlc': 'DLC'}[str(type)]
		except: return str(type).title()

	ret = []
	info = steam_appdetails(apps.keys())
	for appID in info:
		appID = int(appID)
		try:
			data = info[unicode(appID)]['data']

			apps[appID]['type'] = trans(data['type'])
			if apps[appID]['type'] == 'Demo':
				del apps[appID]
				continue
			if apps[appID]['title'] != data['name'].encode('utf-8'):
				print>>sys.stderr, 'Overriding title for %i from search result "%s" to appdetails "%s"' % \
					(appID, apps[appID]['title'], data['name'].encode('utf-8'))
				apps[appID]['title'] = data['name'].encode('utf-8')
			for genre in data['genres']:
				if str(genre['description']) == 'Free to Play':
					apps[appID]['type'] = 'F2P'
		except KeyError as e:
			print>>sys.stderr, 'Skipping %s (%s) - appdetails has no %s' % (appID, apps[appID]['title'], str(e))
			apps[int(appID)]['type'] = '?'
			continue
	return ret

def print_apps(apps, games):
	totals = {}
	print "  appID  | Own | Level | Foil | Type | Title"
	print "---------+-----+-------+------+------+------"
	for (id, app) in sorted(apps.items(), cmp=lambda x,y: cmp(x[1]['title'], y[1]['title'])):
		owned = ' '
		if id in games:
			owned = 'Y'
			totals[app['type']] = totals.get(app['type'], 0) + 1
		level = str(app.get('level', ' '))
		foil = {True: 'Y', False: ' '}[app.get('foil', False)]
		print "%8i |  %s  |   %s   |   %s  | %4s | %s" % (id, owned, level, foil, app['type'], app['title'])
	print
	for type in totals:
		print '%3i %s with Trading Cards Owned' % (totals[type], type)

def usage():
	print "Usage: %s ProfileID" % sys.argv[0]

def main():
	if len(sys.argv) != 2:
		usage()
		sys.exit(1)
	steam_profile = sys.argv[1]

	card_apps = steam_search_card_apps()
	profile_games = steam_profile_games(steam_profile)
	profile_badges = steam_profile_badges(steam_profile)

	for (appID, badge) in profile_badges.items():
		if appID not in card_apps:
			print>>sys.stderr, 'NOTE: App %i (%s) has badges, but not listed as having trading cards in the store' % (appID, badge['title'])
			card_apps[appID] = {}
		badge.update(card_apps[appID])
		card_apps[appID] = badge

	classify_steam_apps(card_apps)
	games = filter(lambda appID: appID in card_apps, profile_games)

	print>>sys.stderr, '%i/%i games matched store trading card query' % (len(games), len(profile_games))

	print_apps(card_apps, games)

if __name__ == '__main__':
	main()
