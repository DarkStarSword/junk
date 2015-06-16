#!/usr/bin/env python

from __future__ import print_function

import os, optparse, glob
import depotcache, acf

from ui import ui_tty as ui

import hashlib
import sys

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

def find_library_root(acf_filename):
	return os.path.relpath(os.path.realpath(os.path.join(
		os.path.curdir, os.path.dirname(acf_filename), '..')))

def find_steam_path_from_registry(opts, reg):
	if opts.verbose:
		ui._print("Looking for steam path from registry...")
	key = reg.OpenKey(reg.HKEY_CURRENT_USER,
			'Software\\Valve\\Steam', 0,
			reg.KEY_READ | reg.KEY_WOW64_32KEY)
	return reg.QueryValueEx(key, 'SteamPath')[0]

def cygwin_path(path):
	import subprocess
	return subprocess.check_output(['cygpath.exe', '-u', path]).strip()

def guess_steam_path_win(opts, translate = lambda x: x):
	for path in [
			r'c:\program files (x86)\steam',
			r'c:\program files\steam',
			r'c:\steam'
			]:
		if opts.verbose:
			ui._print("Searching '%s'..." % translate(path))
		if os.path.isdir(translate(path)):
			return path
	ui._cprint('red', 'Unable to find Steam root - rerun with --steam-root=')
	sys.exit(1)

def find_steam_root(opts, acf_filename = None):
	if acf_filename is not None:
		# If this library has a depotcache, assume it is also the steam root
		# XXX: This could be tricked if someone has created or copied a
		# depotcache folder into the library, or if several steam
		# installations are sharing libraries. In these cases the user
		# will just have to specify --steam-root= to override it.
		library_root = find_library_root(acf_filename)
		if os.path.isdir(os.path.join(library_root, 'depotcache')):
			return library_root
	path = None
	if sys.platform.startswith('linux'):
		path = os.path.expanduser('~/.steam/root')
	elif sys.platform == 'cygwin':
		try:
			import cygwinreg
		except ImportError:
			if opts.verbose:
				ui._print('python-cygwinreg not installed, searching common Steam paths...')
		else:
			if not hasattr(cygwinreg, 'KEY_WOW64_32KEY'):
				cygwinreg.KEY_WOW64_32KEY = 512
			path = cygwin_path(find_steam_path_from_registry(opts, cygwinreg))
		path = path or guess_steam_path_win(opts, cygwin_path)
	elif sys.platform == 'win32':
		import _winreg
		path = find_steam_path_from_registry(opts, _winreg)
		path = path or guess_steam_path_win(opts)
	if path:
		return path
	ui._cprint('red', 'Unable to find Steam root - rerun with --steam-root=')
	sys.exit(1)


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

def verify_file_hash(filename, depot_hash, indent, opts):
	if depot_hash.filetype == 'directory':
		return os.path.isdir(filename)

	s = hashlib.sha1()
	f = open(filename, 'rb')

	bad_found = False

	off = 0
	for chunk in sorted(depot_hash):
		assert(chunk.off == off)
		buf = f.read(chunk.len)
		off += chunk.len
		s.update(buf)

		sha = hashlib.sha1(buf).hexdigest()
		if sha != chunk.sha:
			if opts.verify == 1:
				return False

			if not bad_found:
				ui._cprint('red', ' (BAD CHECKSUM)')
				bad_found = True
			ui._print(indent, end='')
			ui._cprint('red', '%.10i:%.10i found %s expected %s' % \
					(chunk.off, chunk.off+chunk.len, sha, chunk.sha))

	assert(off == depot_hash.filesize)

	if bad_found:
		ui._print(indent, end='')

	eof_garbage = False
	while True:
		buf = f.read(1024*1024)
		if buf == '':
			break
		if not eof_garbage:
			ui._cprint('red', ' (Garbage found at end of file!)', end='')
			eof_garbage = True
		s.update(buf)

	if bad_found:
		return False
	return s.hexdigest() == depot_hash.sha

def verify_manifest_files_exist(manifest_path, game_path, indent, opts):
	def verify_hash():
		if (opts.verify or opts.delete_bad) and not verify_file_hash(filename, depot_hash, indent+g_indent, opts):
			ui._cprint('red', ' (BAD CHECKSUM)', end='')
			return True
	def check_filesize():
		if depot_hash.filetype == 'directory':
			return True
		return filesize == depot_hash.filesize
	def warn_filesize():
		if not check_filesize():
			ui._cprint('red', ' (Filesize != %i, %+i)' % \
					(depot_hash.filesize, filesize - depot_hash.filesize))
			return True

	ok = True
	filenames = FilenameSet()
	for (orig_filename, depot_hash) in depotcache.decode_depotcache(manifest_path):
		filename = os.path.join(game_path, orig_filename.replace('\\', os.path.sep))
		(found, correct, filename, pretty) = insensitive_path(filename, opts)
		filenames.add(filename)

		if opts.file_filter is not None and orig_filename not in opts.file_filter:
			continue

		if found:
			filesize = os.stat(filename).st_size

		corrupt = False

		if not correct:
			ui._print(indent, end='')
			ui._print(pretty, end='')
			if found:
				corrupt = warn_filesize()
				sys.stdout.flush()
				corrupt = corrupt or verify_hash()
				if corrupt and opts.delete_bad:
					ui._cprint('red', ' (DELETED)')
					os.remove(filename)
				else:
					ui._print(' (CASE MISMATCH, ', end='')
					if not opts.rename:
						ui._print('rerun with -r to fix)')
					else:
						ui._print('renamed)')
			else:
				ok = False
				ui._print(' (FILE MISSING)')
		elif opts.verbose > 2 or opts.verify or opts.delete_bad or not check_filesize():
			ui._print(indent + filename, end='')
			corrupt = warn_filesize()
			sys.stdout.flush()
			corrupt = corrupt or verify_hash()
			if corrupt and opts.delete_bad:
				ui._cprint('red', ' (DELETED)', end='')
				os.remove(filename)
			ui._print()
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
		if opts.depot_filter is not None and \
				depot not in opts.depot_filter and \
				manifest not in opts.depot_filter:
			continue
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
		return (True, True, path, path)

	basename = os.path.basename(path)
	dirname = pretty_dirname = os.path.dirname(path)

	if not os.path.isdir(dirname):
		(found, correct, dirname, pretty_dirname) = insensitive_path(dirname, opts)
		if not found:
			return (False, False, dirname, os.path.join(pretty_dirname, basename))

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
				return (True, False, os.path.join(dirname, basename), os.path.join(pretty_dirname, pretty_basename))
			return (True, False, os.path.join(dirname, entry), os.path.join(pretty_dirname, pretty_basename))
	return (False, False, path, ui._ctext('back_red black', path))

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
		install_dir = os.path.basename(app_state['UserConfig']['appinstalldir'])
	# Occasionally the install_dir is the full path in the Windows format.
	# This seems to happen sometimes when moving games from one install to
	# another. AFAICT the full path is never used - the acf file must be in
	# the same steam library as the install regardless, so discard the rest
	# of the path.
	install_dir = install_dir.split('\\')[-1]

	(found, correct, game_path, pretty) = insensitive_path(os.path.join(library_root, 'SteamApps/common/%s' %
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
	if not correct:
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

	if 'appID' in app_state:
		app_id = app_state['appID']
	else:
		app_id = app_state['appid']
        try:
            name = app_state['UserConfig']['name']
        except:
            name = app_state['name']
	ui._print('%s (%s):' % (name, app_id))

	library_root = find_library_root(acf_filename)

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

	ok = check_depots_exist(mounted_depots, managed_depots, opts.steam_root, g_indent*2, opts)
	if not ok: return

	(ok, filenames) = check_all_depot_files_exist(mounted_depots, opts.steam_root, game_path, g_indent*2, opts)
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
	parser.add_option('--verify', action='count',
			help='Validate files integrity (Note: may show false positives if a file is in multiple depots). Specify twice to identify corrupt chunks.')
	parser.add_option('--file-filter', action='append',
			help='Specify file to check. Useful with --verify on large games when the bad files are already known. Can be specified multiple times.')
	parser.add_option('--depot-filter', action='append',
			help='Specify which mounted depots to process. Can be specified multiple times.')
	# '-d': Interractively delete (implies -e) files that not listed in the manifest file
	parser.add_option('-D', '--delete', action='store_true',
			help='Delete any extraneous files, without asking for confirmation (implies -e). CAUTION: Some games may store legitimate files in their directory that are not tracked by Steam which this option will delete. BE CAREFUL WITH THIS OPTION!')
	parser.add_option('--delete-bad', action='store_true',
			help='Delete any files with bad checksums, without asking for confirmation (implies --verify). CAUTION: Some games may store legitimate configuration files in their directory which this option may delete, potentially losing settings. BE CAREFUL WITH THIS OPTION!')
	parser.add_option('-M', '--move', action='store_true', help="Move any extraneous files to SteamApps/common/game~EXTRANEOUS (implies -e). rsync may be used to merge them back into the game directory later.")
	parser.add_option('-U', '--uninstall', action='store_true',
			help="Mark games with bad acf files (Currently that means 0 depotcaches mounted, but that definition may change in the future) as uninstalled. This WILL NOT DELETE THE GAME - it is intended to quickly remove bad acf files that may be interfering with launching or updating particular games. These games will need to be manually re-installed in Steam. (NOTE: Restart Steam afterwards)")
	parser.add_option('--steam-root',
			help="Specify where Steam is installed. This is usually detected automatically based on the acf path, but it may be necessary to specify it if working with games installed in an alternate steam library and this script can't find the game's manifest files.")
	# TODO:
	# '--verify': Mark game as needs verification on next launch (XXX: What option is that in the .acf? XXX: happens if Steam is running at the time?)
	#             Also, when I can do this it might be an idea for some of the above rename/delete options to imply this.
	(opts, args) = parser.parse_args()
	# TODO: If directory specified, interactively ask which game to check by name (maybe change default to do this to)

	if opts.file_filter is not None:
		opts.file_filter = [ x.replace('/', '\\') for x in opts.file_filter ]

	if len(args) == 0:
		if opts.steam_root is None:
			opts.steam_root = find_steam_root(opts)
		args = glob.glob(os.path.join(opts.steam_root, 'SteamApps/appmanifest_*.acf'))
	elif opts.steam_root is None:
		opts.steam_root = find_steam_root(opts, args[0])
	else:
		opts.steam_root = os.path.expanduser(opts.steam_root)

	if opts.verbose:
		ui._print("Using Steam root: '%s'" % opts.steam_root)

	for filename in args:
		check_acf(filename, opts)
		ui._print()

if __name__ == '__main__':
	main()

# vi:noet:ts=8:sw=8
