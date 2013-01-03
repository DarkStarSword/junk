#!/usr/bin/env python

from __future__ import print_function

import os, optparse
import depotcache, acf

from ui import ui_tty as ui

g_indent = '  '
colours = {
	False: 'back_red black',
	True: ''
}

def depot_summary_ok(mounted):
	if len(mounted) > 0:
		return True
	return False

def str_depot_summary(mounted, managed):
	return '%i/%i depotcaches mounted' % (len(mounted), len(managed))

def manifest_filename(depot, timestamp):
	return '%s_%s.manifest' % (depot, timestamp)

def manifest_path(filename):
	return os.path.join(os.path.curdir, '../depotcache/%s' % filename)

def verify_manifest_files_exist(manifest_path, game_path, indent, opts):
	ok = True
	filenames = set()
	for filename in depotcache.decode_depotcache(manifest_path):
		filename = os.path.join(game_path, filename.replace('\\', os.path.sep))
		(found, filename, pretty) = insensitive_path(filename, opts)
		filenames.add(filename)
		if pretty is not None:
			ui._print(indent, end='')
			#ui._cprint('red', filename)
			ui._print(pretty)
			if not found:
				ok = False
		elif opts.verbose > 2:
			ui._print(indent + filename)
	return (ok, filenames)

def check_depots(mounted_depots, managed_depots, game_path, indent, opts):
	ok = True
	filenames = set()
	num_mounted = 0
	for depot in managed_depots:
		if depot in mounted_depots:
			num_mounted += 1
			manifest = manifest_filename(depot, mounted_depots[depot])
			path = manifest_path(manifest)
			if os.path.exists(path):
				if opts.verbose:
					ui._print('%s%s' % (indent, manifest))
				(all_files_exist, manifest_filenames) = \
					verify_manifest_files_exist(path, game_path, indent + g_indent, opts)
				filenames.update(manifest_filenames)
				ok = ok and all_files_exist
			else:
				ui._cprint('red', '%s%s NOT FOUND!' % (indent, manifest))
				ok = False
		elif opts.verbose > 1:
			ui._print('%s%s (not mounted)' % (indent, depot))
	assert(num_mounted == len(mounted_depots))

	return (ok, filenames)

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
			# TODO: if opts.rename: rename...
			return (True, os.path.join(dirname, entry), os.path.join(pretty_dirname, pretty_basename))
	return (False, path, ui._ctext('back_red black', path))


def check_acf(acf_filename, opts):
	app_state = acf.parse_acf(acf_filename)['AppState']

	app_id = app_state['appID']
	name = app_state['UserConfig']['name']
	ui._print('%s (%s):' % (name, app_id))

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
	(found, game_path, pretty) = insensitive_path(os.path.join(os.path.curdir, 'common/%s' %
		install_dir), opts)
	if not found:
		ui._print(g_indent, end='')
		ui._cprint(colours[False], 'Missing game directory', end=': ')
		ui._print(pretty)
		return
	if pretty is not None:
		ui._print(g_indent, end='')
		ui._cprint('back_yellow black', 'WARNING: Case Mismatch', end=': ')
		ui._print(pretty)

	managed_depots = app_state['ManagedDepots'].split(',')
	try:
		mounted_depots = app_state['MountedDepots']
	except KeyError:
		# NOTE: Windows acf files seem to use 'ActiveDepots' instead of
		#       'MountedDepots'. Not sure why the difference.
		# XXX: Double check 'ActiveDepots' is the right key on
		#      my Windows box
		mounted_depots = app_state['ActiveDepots']
	else:
		assert('ActiveDepots' not in app_state)

	ok = depot_summary_ok(mounted_depots)
	colour = colours[ok]
	if opts.verbose or not ok:
		ui._print(g_indent, end='')
		ui._cprint(colour, str_depot_summary(mounted_depots, managed_depots))

	if not ok: return
	(ok, decoders) = check_depots(mounted_depots, managed_depots, game_path, g_indent*2, opts)
	if not ok: return

	# TODO: Search game directory for files NOT listed in any manifest files
	# Should only be done at request since lots of games seem to create log files, etc.
	# TODO: Also detect if two versions of a file exist with differing case
	# TODO: Also add option to purge unlisted files

def main():
	parser = optparse.OptionParser()
	parser.add_option('-v', '--verbose', action='count', help='ui._print out info about things that pasesd. Use multiple times for more info.')
	# TODO:
	# '-r': Automatically rename files with mismatched case and tag the game for needing verification on next launch
	# '-R': Automatically rename files with mismatched case, but do not tag them for verification
	# '-v': Mark game as needs verification on next launch (XXX: What option is that in the .acf? XXX: happens if Steam is running at the time?)
	# '-f': Find any files in the game directories that are not listed in the manifest files
	# '-d': Delete (implies -f) only files that are duplicates by case (XXX: Include game directory) and tag for verification
	# '-D': Delete (implies -f) any files not listed in the manifest file (CAUTION: Some games still have their DLC in the old NCF format, which could cause some required content to be deleted!) And tag for verification
	(opts, args) = parser.parse_args()
	# TODO: If directory specified, interactively ask which game to check by name
	for filename in args:
		check_acf(filename, opts)
		ui._print()

if __name__ == '__main__':
	main()
