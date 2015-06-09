#!/usr/bin/env python
# FIXME: Upgrade dependencies to Python3

from __future__ import print_function

import sys, os, shutil, glob
import acf

# FIXME: Determine this from Steam
main_libraries_paths = [
	'/cygdrive/c/Steam',
	'/cygdrive/d/SteamLibrary',
	'/cygdrive/e/SteamLibrary',
	'/cygdrive/s/SteamLibrary',
]

# FIXME: Pass in with command line or read from config file
update_required_library_path = '/cygdrive/g/SteamLibrary'

# FIXME: Using UNIX paths here!

app_names = {}

class Library(dict):
	def __init__(self, path):
		self.path = path
		for acf_file in glob.glob('{}/SteamApps/*.acf'.format(path)):
			status = acf.parse_acf(acf_file)
			try:
				appid = acf.app_id(status)
				name = acf.app_name(status)
			except KeyError as e:
				print('{} missing key {}'.format(acf_file, str(e)))
				continue
			self[appid] = status
			if appid in app_names and app_names[appid] != name:
				print('{} in multiple libraries with different names: "{}", "{}"'.format(appid, app_names[appid], name))
			app_names[appid] = name

	@property
	def game_path(self):
		return os.path.join(self.path, 'SteamApps', 'common')

def parse_libraries():
	print('Loading libraries...')
	global main_libraries, update_required_library
	main_libraries = map(Library, main_libraries_paths)
	update_required_library = Library(update_required_library_path)

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
	for library in main_libraries + [update_required_library]:
		for appid, app in library.iteritems():
			installdir = acf.install_dir(app)
			if '/' in installdir or '\\' in installdir:
				print('  App ID {} ({}) specifies absolute installdir:'.format(appid, app_names[appid]))
				print('        "{}"'.format(installdir))
				if not os.path.isdir(installdir):
					print("        ... and it's missing")
			else:
				# TODO: Check for matches with differing case
				path = os.path.join(library.game_path, installdir)
				if not os.path.isdir(path):
					print('  App ID {} ({}) missing installation directory:'.format(appid, app_names[appid]))
					print('        "{}"'.format(path))

def check_untracked_directories():
	print('\nChecking for untracked game directories...')
	for library in main_libraries + [update_required_library]:
		tracked_dirs = set([ acf.install_dir(x) for x in library.itervalues() ])
		actual_dirs = set(os.listdir(library.game_path))
		# TODO: Check for matches with differing case
		for untracked in actual_dirs.difference(tracked_dirs):
			print('  Untracked directory: {}'.format(os.path.join(library.game_path, untracked)))

def synchronise_update_required():
	apps_in_update_required = set()
	for acf_file in glob.glob('{}/SteamApps/*.acf'.format(update_required_library_path)):
		# TODO: Check if main library is more recent
		apps_in_update_required.add(os.path.basename(acf_file).lower())

	for library in main_libraries_paths:
		for acf_file in glob.glob('{}/SteamApps/*.acf'.format(library)):
			status = acf.parse_acf(acf_file)
			name = acf.app_name(status)

			try:
				StateFlags = int(status['AppState']['StateFlags'])
			except KeyError as e:
				print('{} missing key {}'.format(acf_file, str(e)))
				continue
			if StateFlags == 4:
				continue
			print('\n{} StateFlags = {}'.format(name, StateFlags))

			acf_basename = os.path.basename(acf_file).lower()
			if acf_basename in apps_in_update_required:
				print('{} already in {}'.format(name, update_required_library_path))
				continue

			game_dir = acf.install_dir(status)
			source = os.path.join(library, 'SteamApps', 'common', game_dir)
			dest = os.path.join(update_required_library_path, 'SteamApps', 'common', game_dir)
			acf_dest = os.path.join(update_required_library_path, 'SteamApps', acf_basename)

			print('Copying {} to {}'.format(name, dest))
			# FIXME: May need to merge existing trees)
			# TODO: If we have all the mounted manifest files, use
			# them to copy only the files that are known to Steam
			try:
				shutil.copytree(source, dest)
				shutil.copy(acf_file, acf_dest)
			except Exception as e:
				print('{} occurred while copying {}: {}'.format(e.__class__.__name__, name, str(e)))

	# TODO: Check if any games in the update required library should be
	# copied back to the regular libraries

def main():
	parse_libraries()
	check_duplicates()
	check_app_dirs()
	check_untracked_directories()
	synchronise_update_required()

if __name__ == '__main__':
	main()
