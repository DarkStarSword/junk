#!/usr/bin/env python

from __future__ import print_function

import os, optparse, glob
import depotcache, acf

from ui import ui_tty as ui

g_indent = '  '
colours = {
	False: 'back_red black',
	True: ''
}

class UnknownLen(list): pass

def depot_summary_ok(mounted):
	if len(mounted) > 0:
		return True
	return False

def str_depot_summary(mounted, managed):
	if isinstance(managed, UnknownLen):
		l = ui._ctext('back_yellow black', '?')
	else:
		l = str(len(managed))
	ret = '%i/%s depotcaches mounted' % (len(mounted), l)
	if len(mounted) == 0:
		ret += ' - Not released on this platform yet?'
	return ret

def manifest_filename(depot, timestamp):
	return '%s_%s.manifest' % (depot, timestamp)

def manifest_path(library_root, filename):
	return os.path.join(library_root, 'depotcache/%s' % filename)

class FilenameSet(set):
	# It may be more efficient to convert the paths to a tree structure,
	# but for the moment this is easier.
	def add(self, element):
		"""
		Override add method to ensure all directory components are also
		added to the set individually.
		"""
		set.add(self, element)
		dirname = os.path.dirname(element)
		if dirname != '':
			self.add(dirname)

def verify_manifest_files_exist(manifest_path, game_path, indent, opts):
	ok = True
	filenames = FilenameSet()
	for filename in depotcache.decode_depotcache(manifest_path):
		filename = os.path.join(game_path, filename.replace('\\', os.path.sep))
		(found, filename, pretty) = insensitive_path(filename, opts)
		filenames.add(filename)
		if pretty is not None:
			ui._print(indent, end='')
			ui._print(pretty, end='')
			if not found:
				ok = False
				ui._print(' (FILE MISSING)')
			else:
				ui._print(' (CASE MISMATCH, ', end='')
				if not opts.rename:
					ui._print('rerun with -r to fix)')
				else:
					ui._print('renamed)')
		elif opts.verbose > 2:
			ui._print(indent + filename)
	return (ok, filenames)

def check_depots_exist(mounted_depots, managed_depots, library_root, indent, opts):
	ok = True
	num_mounted = 0
	for depot in managed_depots:
		if depot in mounted_depots:
			num_mounted += 1
			manifest = manifest_filename(depot, mounted_depots[depot])
			path = manifest_path(library_root, manifest)
			if not os.path.exists(path):
				ui._cprint('red', '%s%s NOT FOUND!' % (indent, manifest), end='')
				ui._print(' (Verify the game cache and try again)')
				ok = False
		elif opts.verbose > 1:
			ui._print('%s%s (not mounted)' % (indent, depot))
	assert(num_mounted == len(mounted_depots))

	return ok

def check_all_depot_files_exist(mounted_depots, library_root, game_path, indent, opts):
	ok = True
	filenames = set()
	for depot in mounted_depots:
		manifest = manifest_filename(depot, mounted_depots[depot])
		path = manifest_path(library_root, manifest)
		if opts.verbose:
			ui._print('%s%s' % (indent, manifest))
		(all_files_exist, manifest_filenames) = \
			verify_manifest_files_exist(path, game_path, indent + g_indent, opts)
		filenames.update(manifest_filenames)
		ok = ok and all_files_exist

	return (ok, filenames)

def mkdir_recursive(path):
	if os.path.isdir(path):
		return

	dirname = pretty_dirname = os.path.dirname(path)
	mkdir_recursive(dirname)
	os.mkdir(path)

def insensitive_path(path, opts):
	if os.path.exists(path):
		return (True, path, None)

	basename = os.path.basename(path)
	dirname = pretty_dirname = os.path.dirname(path)

	if not os.path.isdir(dirname):
		(found, dirname, pretty_dirname) = insensitive_path(dirname, opts)
		if not found:
			return (False, dirname, os.path.join(pretty_dirname, basename))

	pretty_basename = ''
	for entry in os.listdir(dirname):
		if entry.lower() == basename.lower():
			for i in range(len(entry)):
				if entry[i] != basename[i]:
					pretty_basename += ui._ctext('back_yellow black', entry[i])
				else:
					pretty_basename += entry[i]
			if opts.rename:
				os.rename(os.path.join(dirname, entry), os.path.join(dirname, basename))
				return (True, os.path.join(dirname, basename), os.path.join(pretty_dirname, pretty_basename))
			return (True, os.path.join(dirname, entry), os.path.join(pretty_dirname, pretty_basename))
	return (False, path, ui._ctext('back_red black', path))

def find_extra_files(game_path, known_filenames, indent, opts):
	known_filenames_l = set(map(str.lower, known_filenames))
	if opts.move:
		dest_root = os.path.realpath(os.path.join(game_path, '..'))
		dest_root = os.path.join(dest_root, os.path.basename(game_path) + '~EXTRANEOUS')
	for (root, dirs, files) in os.walk(game_path, topdown = not (opts.delete or opts.move)):
		for fname in dirs + files:
			path = os.path.join(root, fname)
			if path in known_filenames:
				continue
			ui._print(indent, end='')
			extra='\n'
			if opts.move:
				if fname in dirs:
					try:
						os.rmdir(path)
						extra = ' (REMOVED)\n'
					except OSError as e:
						extra = ' %s\n' % str(e)
				else:
					dest = os.path.join(dest_root, os.path.relpath(path, game_path))
					try:
						mkdir_recursive(os.path.dirname(dest))
						os.rename(path, dest)
						extra = '\n%s  --> %s\n' % (indent, os.path.relpath(dest))
					except OSError as e:
						extra = ' %s\n' % str(e)
			elif opts.delete:
				extra = ' (DELETED)\n'
				if fname in dirs:
					os.rmdir(path)
				else:
					os.remove(path)
			if path.lower() in known_filenames_l:
				ui._cprint('back_blue yellow', path, end=' (DUPLICATE WITH DIFFERING CASE)%s' % extra)
			else:
				ui._cprint('back_blue yellow', path, end=extra)

def find_game_path(app_state, library_root, acf_filename, opts):
	# XXX TODO: acf games can be installed in other libraries, I need to
	# try it to find if that would change this logic.
	#
	# NOTE: There is also a UserConfig.appinstalldir, however it may be
	# unreliable if the acf has been copied from another location and the
	# game has not yet been launched.
	install_dir = app_state['installdir']
	if install_dir == '':
		ui._cprint('yellow', g_indent + 'WARNING: Blank installdir in %s, trying UserConfig.appinstalldir...' % acf_filename)
		# FIXME: This may be in the Windows format which will probably break this!
		install_dir = os.path.basename(app_state['UserConfig']['appinstalldir'])

	(found, game_path, pretty) = insensitive_path(os.path.join(library_root, 'SteamApps/common/%s' %
		install_dir), opts)
	if found:
		# TODO: Warn if a second directory exists with the same name
		# but differing case, since that may confuse Steam or the game
		pass
	else:
		ui._print(g_indent, end='')
		ui._cprint(colours[False], 'Missing game directory', end=': ')
		ui._print(pretty)
		return None
	if pretty is not None:
		ui._print(g_indent, end='')
		ui._cprint('back_yellow black', 'WARNING: Case Mismatch', end='')
		if not opts.rename:
			ui._print(' (rerun with -r to fix)', end='')
		ui._print(': ', end='')
		ui._print(pretty)
	return game_path

def get_mounted_depots(app_state):
	try:
		mounted_depots = app_state['MountedDepots']
	except KeyError:
		# NOTE: Windows acf files seem to use 'ActiveDepots' instead of
		#       'MountedDepots'. Not sure why the difference.
		# XXX: Double check 'ActiveDepots' is the right key on
		#      my Windows box
		return app_state['ActiveDepots']
	assert('ActiveDepots' not in app_state)
	return mounted_depots

def check_acf(acf_filename, opts):
	app_state = acf.parse_acf(acf_filename)['AppState']

	app_id = app_state['appID']
	name = app_state['UserConfig']['name']
	ui._print('%s (%s):' % (name, app_id))

	library_root = os.path.relpath(os.path.realpath(os.path.join(
		os.path.curdir, os.path.dirname(acf_filename), '..')))

	game_path = find_game_path(app_state, library_root, acf_filename, opts)
	if game_path is None: return

	mounted_depots = get_mounted_depots(app_state)
	try:
		managed_depots = app_state['ManagedDepots'].split(',')
	except KeyError:
		#ui._cprint('back_yellow black', 'WARNING: No ManagedDepots, using MountedDepots instead!')
		managed_depots = UnknownLen(mounted_depots.keys())

	ok = depot_summary_ok(mounted_depots)
	colour = colours[ok]
	if opts.verbose or not ok:
		ui._print(g_indent, end='')
		ui._cprint(colour, str_depot_summary(mounted_depots, managed_depots))
	if not ok:
		if opts.uninstall:
			ui._print(g_indent, end='')
			path = os.path.join(os.path.curdir, acf_filename)
			os.rename(path, path + '~')
			ui._cprint('back_yellow black', 'UNINSTALLED!')
		return

	ok = check_depots_exist(mounted_depots, managed_depots, library_root, g_indent*2, opts)
	if not ok: return

	(ok, filenames) = check_all_depot_files_exist(mounted_depots, library_root, game_path, g_indent*2, opts)
	if opts.extra or opts.delete or opts.move:
		if opts.verbose: # So they don't appear to be under a manifest heading
			ui._print(g_indent*2 + 'Untracked files:')
		find_extra_files(game_path, filenames, g_indent*3, opts)
	if not ok: return

	ui._cprint('green', 'OK')

def main():
	parser = optparse.OptionParser()
	parser.add_option('-v', '--verbose', action='count',
			help='Print out info about things that pasesd. Use multiple times for more info.')
	parser.add_option('-r', '--rename', action='store_true',
			help='Rename files & directories to correct case mismatches')
	parser.add_option('-e', '--extra', '--extraneous', action='store_true',
			help='List any files in the game directory that are not tracked by any manifest files. Extraneous files are highlighted in ' + \
				ui._ctext('back_blue yellow', 'blue'))
	# '-d': Interractively delete (implies -e) files that not listed in the manifest file
	parser.add_option('-D', '--delete', action='store_true',
			help='Delete any extraneous files, without asking for confirmation (implies -e). CAUTION: Some games may store legitimate files in their directory that are not tracked by Steam which this option will delete. Also beware that a few games (e.g. Borderlands) still have their DLC managed by the legacy NCF format, which this script is not aware of and could therefore delete required files. BE CAREFUL WITH THIS OPTION!')
	parser.add_option('-M', '--move', action='store_true', help="Move any extraneous files to SteamApps/common/game~EXTRANEOUS (implies -e). rsync may be used to merge them back into the game directory later.")
	parser.add_option('-U', '--uninstall', action='store_true',
			help="Mark games with bad acf files (Currently that means 0 depotcaches mounted, but that definition may change in the future) as uninstalled. This WILL NOT DELETE THE GAME - it is intended to quickly remove bad acf files that may be interfering with launching or updating particular games. These games will need to be manually re-installed in Steam. (NOTE: Restart Steam afterwards)")
	# TODO:
	# '--verify': Mark game as needs verification on next launch (XXX: What option is that in the .acf? XXX: happens if Steam is running at the time?)
	#             Also, when I can do this it might be an idea for some of the above rename/delete options to imply this.
	(opts, args) = parser.parse_args()
	# TODO: If directory specified, interactively ask which game to check by name (maybe change default to do this to)
	if len(args) == 0:
		args = glob.glob(os.path.expanduser('~/.steam/root/SteamApps/appmanifest_*.acf'))
	for filename in args:
		check_acf(filename, opts)
		ui._print()

if __name__ == '__main__':
	main()
