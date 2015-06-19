#!/usr/bin/env python
# FIXME: Upgrade dependencies to Python3

from __future__ import print_function

import sys, os, shutil, re, argparse
import acf
import distutils.dir_util, distutils.file_util

# FIXME: Determine this from Steam
main_libraries_paths = [
	'/cygdrive/c/Steam',
	'/cygdrive/d/SteamLibrary',
	'/cygdrive/e/SteamLibrary',
	'/cygdrive/s/SteamLibrary',
]

# FIXME: Pass in with command line or read from config file
update_required_library_path = '/cygdrive/g/SteamLibrary'

# http://forums.steampowered.com/forums/showthread.php?t=2952766
class AppState(object):
	Invalid        = 0x000000
	Uninstalled    = 0x000001
	UpdateRequired = 0x000002
	FullyInstalled = 0x000004
	Encrypted      = 0x000008
	Locked         = 0x000010
	FilesMissing   = 0x000020
	AppRunning     = 0x000040
	FilesCorrupt   = 0x000080
	UpdateRunning  = 0x000100
	UpdatePaused   = 0x000200
	UpdateStarted  = 0x000400
	Uninstalling   = 0x000800
	BackupRunning  = 0x001000
	Reconfiguring  = 0x010000
	Validating     = 0x020000
	AddingFiles    = 0x040000
	Preallocating  = 0x080000
	Downloading    = 0x100000
	Staging        = 0x200000
	Committing     = 0x400000
	UpdateStopping = 0x800000

	# Any others?
	CopyToUpdateRequired = UpdateRequired | FilesMissing | FilesCorrupt

# FIXME: Using UNIX paths here!

class App(object):
	def __init__(self, acf_file, library, add_to_apps):
		self.acf_file = acf_file
		self.library = library
		self.status = acf.parse_acf(acf_file)

		# Sanity check if the acf file appears to be valid before we add it to any lists:
		self.appid
		self.name

		if self.appid in app_names and app_names[self.appid] != self.name:
			print('{} in multiple libraries with different names: "{}", "{}"'.format(self.appid, app_names[self.appid], self.name))
		app_names[self.appid] = self.name

		if add_to_apps:
			if self.appid not in apps:
				apps[self.appid] = []
			apps[self.appid].append(self)

	@property
	def appid(self):
		try:
			return self.status['AppState']['appID']
		except:
			return self.status['AppState']['appid']

	@property
	def name(self):
		try:
			return self.status['AppState']['name']
		except:
			try:
				return self.status['AppState']['UserConfig']['name']
			except:
				try:
					return self.appid
				except KeyError as e:
					print("Unable to identify app name. Missing key {}. Contents: {}".format(str(e), self.status))
					return None

	@property
	def install_dir(self):
		return self.status['AppState']['installdir']

	@property
	def path(self):
		return os.path.join(self.library.game_path, self.install_dir)

	@property
	def acf_path(self):
		return os.path.join(self.library.acf_path, self.acf_file)

	@property
	def state_flags(self):
		return int(self.status['AppState']['StateFlags'])

	@property
	def last_updated(self):
		return int(self.status['AppState']['LastUpdated'])

apps = {}
app_names = {}

class Library(dict):
	def __init__(self, path, add_to_apps=True):
		self.path = path
		SteamApps = os.path.join(path, 'SteamApps')
		files = os.listdir(os.path.join(path, 'SteamApps'))
		pattern = re.compile(r'^appmanifest_[0-9]+.acf$', re.IGNORECASE)
		for file in [ x for x in files if pattern.match(x) ]:
			acf_file = os.path.join(SteamApps, file)
			try:
				app = App(acf_file, self, add_to_apps)
			except KeyError as e:
				print('{} missing key {}'.format(acf_file, str(e)))
				continue
			self[app.appid] = app

	@property
	def acf_path(self):
		return os.path.join(self.path, 'SteamApps')

	@property
	def game_path(self):
		return os.path.join(self.path, 'SteamApps', 'common')

def parse_libraries():
	print('Loading libraries...')
	global main_libraries, update_required_library, all_libraries
	main_libraries = map(Library, args.library)
	if args.updates_library:
		update_required_library = Library(args.updates_library, False)
		all_libraries = main_libraries + [update_required_library]
	else:
		update_required_library = None
		all_libraries = main_libraries

def check_duplicates():
	print('Checking for AppIDs installed in multiple libraries...')
	duplicates = {}
	for i, lib1 in enumerate(main_libraries):
		for lib2 in main_libraries[i+1:]:
			intersection = set(lib1).intersection(lib2)
			for appid in intersection:
				if appid not in duplicates:
					duplicates[appid] = set()
				duplicates[appid].add(lib1.path)
				duplicates[appid].add(lib2.path)
	if duplicates:
		for appid in duplicates:
			print('  App ID {} ({}) found in: {}'.format(appid, app_names[appid], ', '.join(sorted(duplicates[appid]))))

def check_app_dirs():
	print('\nChecking for bad or missing install dirs...')
	for library in all_libraries:
		for appid, app in library.iteritems():
			installdir = app.install_dir
			if '/' in installdir or '\\' in installdir:
				print('  App ID {} ({}) in {} specifies absolute installdir:'.format(appid, app_names[appid], library.path))
				print('        "{}"'.format(installdir))
				if not os.path.isdir(installdir):
					print("        ... and it's missing")
			else:
				# TODO: Check for matches with differing case
				path = os.path.join(library.game_path, installdir)
				if not os.path.isdir(path):
					print('  App ID {} ({}) in {} missing installation directory:'.format(appid, app_names[appid], library.path))
					print('        "{}"'.format(path))

def check_untracked_directories():
	print('\nChecking for untracked game directories...')
	for library in all_libraries:
		tracked_dirs = set(map(str.lower, [ x.install_dir for x in library.itervalues() ]))
		actual_dirs = set(map(str.lower, os.listdir(library.game_path)))
		for untracked in actual_dirs.difference(tracked_dirs):
			print('  Untracked directory: {}'.format(os.path.join(library.game_path, untracked)))

def synchronise_update_required():
	print('\nSynchronising update library...')
	for library in main_libraries:
		for appid, app in library.iteritems():
			if (app.state_flags & AppState.CopyToUpdateRequired) == 0:
				continue
			print('\n  {} StateFlags = {}'.format(app.name, app.state_flags))

			if appid in update_required_library:
				print('  {} already in {}'.format(app.name, update_required_library.path))
				continue

			game_dir = app.install_dir
			source = os.path.join(library.game_path, game_dir)
			dest = os.path.join(update_required_library.game_path, game_dir)
			acf_basename = os.path.basename(app.acf_file).lower()
			acf_dest = os.path.join(update_required_library.acf_path, acf_basename)

			print('  Copying {} to {}'.format(app.name, dest))
			# FIXME: May need to merge existing trees)
			# TODO: If we have all the mounted manifest files, use
			# them to copy only the files that are known to Steam
			try:
				shutil.copytree(source, dest)
				shutil.copy(app.acf_file, acf_dest)
			except Exception as e:
				print('  {} occurred while copying {}: {}'.format(e.__class__.__name__, app.name, str(e)))

def synchronise_update_required_reverse():
	print('\nSynchronising back updates...')
	for appid, app in update_required_library.iteritems():
		if app.state_flags != AppState.FullyInstalled:
			continue

		if appid not in apps:
			print('\n  App ID {} ({}) not found in any main library, not synchronising!'.format(appid, app.name))
			continue

		if len(apps[appid]) != 1:
			print('\n  App ID {} ({}) in multiple main libraries, not synchronising!'.format(appid, app.name))
			continue

		installed = apps[appid][0]
		if installed.status == app.status:
			# print('\n  {} ({}) is up to date'.format(appid, app.name))
			continue

		if installed.last_updated >= app.last_updated:
			print('\n  Local install of app {} ({}) is more recent, not synchronising!'.format(appid, app.name))
			continue

		print('\n  Copying {} ({}) to {}...'.format(app.name, appid, installed.path))

		# TODO: Do this safely if Steam is running. Not sure what the
		# best option is for that - if nothing else I might be able to
		# rename the target directory, tell Steam to uninstall it, copy
		# the files, rename it back then restart Steam.

		# None of the built in copy method in Python are exactly what I
		# want. This will do for now, but eventually I'd like to use my
		# own logic to decide which files to update - if the filesize
		# or SHA1 differs (either obtained from a manifest file or
		# reading the file) it should be updated. If all manifest files
		# are present we can also skip (or even remove) untracked files.
		distutils.dir_util.copy_tree(app.path, installed.path, update=1)
		distutils.file_util.copy_file(app.acf_path, installed.acf_path)

def parse_args():
	global args

	parser = argparse.ArgumentParser(description = 'Steam library manager')
	parser.add_argument('-l', '--library', action='append',
			help='Location of a regular Steam library to process, can specify multiple times')
	parser.add_argument('--updates-library',
			help='A special library that is intended for games that require updates, such as a library on a portable hard drive.')
	parser.add_argument('--check', action='store_true',
			help='Check the libraries for common problems')
	parser.add_argument('--copy-update-required', action='store_true',
			help='Copy any games that require updates to the library specified by --updates-library')
	parser.add_argument('--sync-updated', action='store_true',
			help='Copy any games that have been updated in the library specified by --updates-library back to the main library')
	args = parser.parse_args()

	# TODO: Replace with config file
	if not args.library and not args.updates_library:
		args.library = main_libraries_paths
		args.updates_library = update_required_library_path

	if not args.check and \
	   not args.copy_update_required and \
	   not args.sync_updated:
		args.check = True
		if args.updates_library:
			args.copy_update_required = True
			args.sync_updated = True

def main():
	parse_args()
	parse_libraries()

	if args.check:
		check_duplicates()
		check_app_dirs()
		check_untracked_directories()
		# TODO: check_stale_downloads()

	if args.copy_update_required:
		synchronise_update_required()

	if args.sync_updated:
		synchronise_update_required_reverse()

if __name__ == '__main__':
	main()
