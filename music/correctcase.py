#!/usr/bin/python

# Copyright 2009 Ian Munsie
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

#Any words that should not be capitalised unless they are the first or (rarely) last word in the title:
#Based loosely on http://www.searchenginejournal.com/title-capitalization-in-the-engligh-language/4882/

capitaliserules = ['and', 'but', 'or', 'nor', 'to', 'over', 'an', 'a', 'the', 'for', 'yet', 'so', 'because', 'if', 'so that', 'after', 'when', 'although', 'while', 'even though', 'of', 'in', 'on', 'with', 'as', 'by', 'at', 'from', 'vs.']

#More complex capitalisation rules should be defined here in pairs of regular expressions and the capitalisation rules they follow - l to convert to lower case, . to leave alone. There should be twice plus one as many letters in the second string as there are groups in the regular expression - before, group, between, group, between, group, after
capitaliserulesre = [["both (.*) and", "l.l"], ["either (.*) or", "l.l"], ["neither (.*) nor", "l.l"], ["not( only)+ (.*) but (.* )(also)+", "ll..l..l."]]

#Any words that should not be corrected such as acronyms (NOTE that matching words will NOT be corrected into these, also note that the algorithm already has some fuzzy detection for acronyms that include fullstops):
specialwords = ['TV', 'OST', 'EP', 'OK', 'US', 'CIA', 'AM', 'PM', 'DJ']

#I'm keeping this separate because they are specific artists:
specialwords.extend(['EL', 'DragonForce', 'dreamSTATE', 'MyEarthDream', 'ABBA', 'JauwizD', 'JT', 'DiCola', 'DarkeSword'])

#Any of these characters in the resulting filename for a rename operation will be replaced with safechar:
unsafechars = ['*', '?', '<', '>', '|', '"', ':', '/', '\\']
safechar = '_'

#These regular expressions should match title separators - such as those enclosed in brackets, after a slash and so forth.
innertitles = [ "\((.*?)\)", "\[(.*?)\]", '"(.*?)"', "^(.*? |)'(.*?)'( .*?|)$", "/(.*)", "- ?(.*)", "; ?(.*)",": (.*)", "\. (.*)" ]

defaultrenamepattern = ["%n - %t", "%t"]

import os
import sys
import fnmatch
import eyeD3
import re
from optparse import OptionParser

warntitle = []
warnalbum = []
warnartist = []
warnrename = []
corruptfiles = []

def isacronym(word):
  "attempts to determine if the word is an acronym - ie, all upper case with full stops after letters"
  return re.match("^([A-Z]+\.)+$", word)

def isinnertitle(word):
  "determines if the word satisfies any of the rules to be considered an inner title"
  for itit in innertitles:
    #if re.match(itit, word): return True
    if re.search(itit, word): return True
  return False

def isspecialword(word):
  "determines if the word is in the special list, disregarding punctuation"
  for w in specialwords:
    if re.match("^[^A-Za-z0-9]*%s[^A-Za-z0-9]*$" % w, word): return True
  return False

def isromannumeral(word):
  "attempts to determine if the word is a Roman Numeral, which should remain capitalised. This is a bit fuzzy and will overmatch (IVVIIII is valid), I *think* it won't undermatch (where word < 4000), but it hopefully is close enough. I'm just adding punctuation to this list as I come across it"
  if not re.match("[IVXLCDM:\(\)]+", word): return False
  return re.match("^\(?I{0,4}(VI{0,4})?X{0,4}(LX{0,4})?C{0,4}(DC{0,4})?M*I{0,4}(VI{0,4})?X{0,4}(LX{0,4})?C{0,4}(DC{0,4})?I{0,4}(VI{0,4})?X{0,4}(LX{0,4})?I{0,4}(VI{0,4})?\)?:?$", word)

def isMac(word):
  "Determines if the word is a Mc or Mac name"
  return re.match("^Ma?c[A-Z][a-z].*$", word)

def innertitle(match):
  "Match a title in a title (e.g. encased in brackets), and capitalise it independently"
  pos = 0
  result = ''
  for group in range(len(match.groups())):
    result += match.group()[pos : match.start(group + 1) - match.start()]
    result += fixcase(match.group()[match.start(group + 1) - match.start() : match.end(group + 1) - match.start() ])
    pos = match.end(group + 1) - match.start()
  result += match.group()[pos:]
  return result

def captitle(title):
  "Capitalise the title with simple rules"
  words = title.split(' ')
  #working = ' '.join([x if x in specialwords or isacronym(x) or isromannumeral(x) or isMac(x) or isinnertitle(x) else x.lower() if i != 0 and i != len(words) - 1 and x.lower() in capitaliserules else x.capitalize() for i,x in enumerate(words)])
  working = ' '.join([x if  isacronym(x) or isromannumeral(x) or isMac(x) or isspecialword(x) else x.lower() if i != 0 and i != len(words) - 1 and x.lower() in capitaliserules else x.capitalize() for i,x in enumerate(words)])
  #working = ' '.join([x if x in specialwords or isacronym(x) else x.lower() if i != 0 and i != len(words) - 1 and x.lower() in capitaliserules else x.capitalize() for i,x in enumerate(words)])
  #Look for various types of title dividers:
  for intit in innertitles:
    working = re.sub(intit, innertitle, working)
  return working

currentcaserule = ''
def lowerrepl(match):
  "Take a regular expression match and change the case of each section based on the currentcaserule global"
  global currentcaserule
  pos = 0
  result = ''
  for group in range(len(match.groups())):
    temp = match.group()[pos : match.start(group + 1) - match.start()]
    if currentcaserule[group * 2] == 'l': temp = temp.lower()
    result = result + temp
    temp = match.group()[match.start(group + 1) - match.start() : match.end(group + 1) - match.start() ]
    if currentcaserule[group * 2 + 1] == 'l': temp = temp.lower()
    result = result + temp
    pos = match.end(group + 1) - match.start()
  temp = match.group()[pos:]
  if currentcaserule[len(match.groups())] == 'l': temp = temp.lower()
  result = result + temp
  return result

def fixcase(title):
  "Take a title and correct it's capitalisation. The first and last words are always capitalised as is every word _not_ present in the capitaliserules arrary"
  global currentcaserule
  title = captitle(title)
  for rule in capitaliserulesre:
    p = re.compile(" %s " % rule[0], re.IGNORECASE)
    currentcaserule = rule[1]
    title = p.sub(lowerrepl, title)
  return title

def gen_find_mp3(top, pattern):
  "Generator to find files matching pattern under top"
  for path, dirlist, filelist in os.walk(top):
    for name in fnmatch.filter(filelist, pattern):
      yield os.path.join(path,name)

def check_mp3_filename(mp3):
  "Check if the title, album and artist are present in the filename"
  if not eyeD3.isMp3File(mp3):
    print "---ERROR: %s is not a valid MP3" % mp3
    return
  mp3file = None
  mp3file = eyeD3.Mp3AudioFile(mp3)
  tag = mp3file.getTag()
  if not tag:
    print "---ERROR processing %s" % mp3
    return
  title = tag.getTitle().replace('/', safechar)
  album = tag.getAlbum().replace('/', safechar)
  artist = tag.getArtist().replace('/', safechar)
  #Make filename safe:
  for unsafe in unsafechars:
    title = title.replace(unsafe, safechar)
    album = album.replace(unsafe, safechar)
    artist = artist.replace(unsafe, safechar)
  title = re.sub('\.+$', '', title)
  album = re.sub('\.+$', '', album)
  artist = re.sub('\.+$', '', artist)
  filename = os.path.realpath(mp3)
  try:
    #if artist and filename.find(artist) == -1: print "Check %s: %s" % (filename, artist)
    if artist and (filename.find(artist) == -1 and (not artist.startswith("The ") or filename.find(artist[4:] + ", The") == -1)): print "Check %s: %s" % (filename, artist)
    if album and filename.find(album) == -1: print "Check %s: %s - %s" % (filename, artist, album)
    if title and filename.find(title) == -1: print "Check %s: %s - %s - %s" % (filename, artist, album, title)
  except:
    print "ERROR trying to display", mp3

def fix_mp3_case(mp3, prompt, rename, renamepattern):
  "Uses eyeD3 to extract the title, album and artist names and correct their capitalisation"
  updated = False
  if not eyeD3.isMp3File(mp3):
    corruptfiles.append(mp3)
    print "---ERROR: %s is not a valid MP3" % mp3
    return
  mp3file = None
  try:
    mp3file = eyeD3.Mp3AudioFile(mp3)
  except:
    corruptfiles.append(mp3)
    print "---ERROR processing %s" % mp3
    return
  tag = mp3file.getTag()
  if not tag:
    corruptfiles.append(mp3)
    print "---ERROR processing %s" % mp3
    return
  title = tag.getTitle()
  album = tag.getAlbum()
  artist = tag.getArtist()
  fixedtitle = fixcase(title)
  fixedalbum = fixcase(album)
  fixedartist = fixcase(artist)
  if title != fixedtitle or album != fixedalbum or artist != fixedartist:
    print 'About to alter "%s" as follows:' % mp3
    if title != fixedtitle:
      print ' Title: "%s"\n    ==> "%s"' % (title, fixedtitle)
    if album != fixedalbum:
      print ' Album: "%s"\n    ==> "%s"' % (album, fixedalbum)
    if artist != fixedartist:
      print 'Artist: "%s"\n    ==> "%s"' % (artist, fixedartist)
    if not prompt or raw_input("Is that OK? ").lower().find('y') == 0:
      tag.setTitle(fixedtitle)
      tag.setAlbum(fixedalbum)
      tag.setArtist(fixedartist)
      tag.update()
      updated = True
  if rename:
    renamedpatternmatched = False
    for renpat in renamepattern:
      #eyeD3 replaces / with -, but I want it replaced with _ like Amarok:
      tag.setTitle(tag.getTitle().replace('/', safechar))
      tag.setAlbum(tag.getAlbum().replace('/', safechar))
      tag.setArtist(tag.getArtist().replace('/', safechar))
      renamestr = tag.tagToString(renpat)
      if renamestr.find("%") == -1:
        renamedpatternmatched = True
        #Make filename safe:
        for unsafe in unsafechars:
          renamestr = renamestr.replace(unsafe, safechar)
        #Remove trailing dots if present to mimic amarok
        renamestr = re.sub('\.+$', '', renamestr)
        filename = os.path.basename(mp3file.fileName)
        if filename != renamestr + ".mp3":
          try:
            sys.stdout.write('ABOUT TO RENAME: "%s"\n             TO: "%s"' % (filename, renamestr + ".mp3"))
          except:
            sys.stdout.write('ABOUT TO RENAME: "%s"\n           TO: "%r" (Note: Unprintable characters should not cause any issues during rename)' % (filename, renamestr + ".mp3"))
          if not prompt or raw_input(", OK? ").lower().find('y') == 0:
            if not prompt: print
            mp3file.rename(renamestr, sys.getfilesystemencoding())
        if updated:
          #Look for changed values that were not included in the rename:
          if title != fixedtitle and renpat.find("%t") == -1:
            temp = "FROM: %s - %s - %s\n ===> %s - %s - %s" % (artist, album, title, fixedartist, fixedalbum, fixedtitle)
            if temp not in warntitle: warntitle.append(temp)
          if album != fixedalbum and renpat.find("%a") == -1:
            temp = "FROM: %s - %s\n ===> %s - %s" % (artist, album, fixedartist, fixedalbum)
            if temp not in warnalbum: warnalbum.append(temp)
          if artist != fixedartist and renpat.find("%A") == -1:
            temp = "FROM: %s\n ===> %s" % (artist, fixedartist)
            if temp not in warnartist: warnartist.append(temp)
        break
    if not renamedpatternmatched:
      warnrename.append("FROM: %s - %s - %s\n ===> %s - %s - %s" % (artist, album, title, fixedartist, fixedalbum, fixedtitle))

def main():
  parser = OptionParser(usage="usage: %prog [options] [files]")
  parser.add_option("-y", "--yes", action="store_false", dest="prompt", default=True, help="Don't prompt to change tags or rename, just do it")
  parser.add_option("-r", "--rename", action="store_true", dest="rename", default=False, help="Enable renaming the file based on a particular pattern")
  parser.add_option("-p", "--pattern", action="append", dest="renamepattern", metavar="PATTERN", help="Specify the pattern to rename the file to. Can be specified multiple times to specify fallback patterns in case a pattern cannot be fully expanded. Uses the same options as eyeD3 --rename (default: %s)" % repr(defaultrenamepattern))
  parser.add_option("-k", "--check", action="store_true", dest="check", default=False, help="Check if title, album and artist tags are present in the path instead of altering")
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False, help="Output each file as it is processed")
  (options, args) = parser.parse_args()
  if not options.renamepattern:
    options.renamepattern = defaultrenamepattern

  try:
    if len(args):
      for pattern in args:
        mp3s = gen_find_mp3('.', pattern)
        for mp3 in mp3s:
          if options.verbose:
            print "Processing", mp3
          if options.check:
            check_mp3_filename(mp3)
          else:
            fix_mp3_case(mp3, options.prompt, options.rename, options.renamepattern)
    else:
      mp3s = gen_find_mp3('.', "*.mp3")
      for mp3 in mp3s:
        if options.verbose:
          print "Processing", mp3
        if options.check:
          check_mp3_filename(mp3)
        else:
          fix_mp3_case(mp3, options.prompt, options.rename, options.renamepattern)
  except KeyboardInterrupt:
    print "Interrupted"
  if options.rename:
    if warntitle:
      print "\n---WARNING: The following TITLES were altered, but the rename operation DID NOT include this data:"
      for title in warntitle:
        print title
    if warnalbum:
      print "\n---WARNING: The following ALBUMS were altered, but the rename operation DID NOT include this data:"
      for album in warnalbum:
        print album
    if warnartist:
      print "\n---WARNING: The following ARTISTS were altered, but the rename operation DID NOT include this data:"
      for artist in warnartist:
        print artist
    if warnrename:
      print "\n---WARNING: The following files _may_ have been altered, but the rename operation WAS UNABLE TO MATCH ENOUGH DATA, SO THE FILES WERE NOT RENAMED:"
      for ren in warnrename:
        print ren
  if corruptfiles:
    print "\n---WARNING: The following files had problems (possibly not valid mp3s or corrupt files) and were not changed:"
    for crpt in corruptfiles:
      print crpt

if __name__ == "__main__":
  main()
