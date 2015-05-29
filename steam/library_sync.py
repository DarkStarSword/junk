#!/usr/bin/env python
# FIXME: Upgrade dependencies to Python3

import sys, os, shutil, glob
import acf

# FIXME: Determine this from Steam
main_libraries = [
	'/cygdrive/c/Steam',
	'/cygdrive/d/SteamLibrary',
	'/cygdrive/e/SteamLibrary',
	'/cygdrive/s/SteamLibrary',
]

# FIXME: Pass in with command line or read from config file
update_required_library = '/cygdrive/g/SteamLibrary'

# FIXME: Using UNIX paths here!

def main():
	apps_in_update_required = set()
	for acf_file in glob.glob('{}/SteamApps/*.acf'.format(update_required_library)):
		# TODO: Check if main library is more recent
		apps_in_update_required.add(os.path.basename(acf_file).lower())

	for library in main_libraries:
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
				print('{} already in {}'.format(name, update_required_library))
				continue

			game_dir = acf.install_dir(status)
			source = os.path.join(library, 'SteamApps', 'common', game_dir)
			dest = os.path.join(update_required_library, 'SteamApps', 'common', game_dir)
			acf_dest = os.path.join(update_required_library, 'SteamApps', acf_basename)

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

if __name__ == '__main__':
	main()
