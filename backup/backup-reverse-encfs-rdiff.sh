#!/bin/sh

# Uses reverse encfs to create an encrypted view of the directory to be backed
# up, then runs rdiff-backup to back it up to a remote server.
#
# The .encfs6.xml file is backed up separately as that is ABSOLUTELY REQUIRED
# to be able to recover the backup later.
#
# To use, edit and fill in at least the SOURCE and DEST. CRYPT should point to
# an empty directory that you own outside of the SOURCE.  Optionally you may
# specify a rsync style FILTER file and period to REMOVE old incremental
# backups.
#
# The first time it is run, if the SOURCE directory does not already have a
# reverse encfs set up it will be created with some default options. DEST
# should not exist, or at least should be empty. The script does not verify
# this, and bad things can happen if DEST contains a prior rdiff-backup
# of the SOURCE encrypted with a different key - rdiff-backup will not identify
# that the files are encrypted with a new key and won't backup anything that
# hasn't changed. Just don't do this.
#
# For non-interactive use, the password may also be read from a file specified
# on the command line.



#
# Source directory to backup
# NOTE: Don't add trailing slashes here!
#
SOURCE=$HOME

#
# Destination for the backup. FILL THIS IN!!
# Use rdiff-backup format, i.e. two colons to separate server from directory
# NOTE: Don't add trailing slashes here!
#
#DEST=server::backup/my_home_backup

#
# rsync style filter file for including/excluding files
# If you use filename encryption you would have to translate the filenames. If
# you want to use a pattern filter you must turn filename encryption off.
#
#FILTER=$HOME/.backup-filter

#
# Remove incremental backups older than this
#
REMOVE=2W

#
# Source and dest for backing up the encfs6.xml file - you NEED this file to
# be able to recover your backup, so make sure this is backed up somewhere!
#
ENCFS_XML_SRC="$SOURCE/.encfs6.xml"
ENCFS_XML_DEST=$(echo $DEST|sed 's/::/:/').encfs6.xml

#
# Directory to use as a temporary mountpoint for reverse encfs. Must exist & be
# owned by you.  NOTE: Don't add trailing slashes here!
#
CRYPT=$HOME-crypt-view



if [ -z "$SOURCE" ]; then
	echo "Please fill in SOURCE and rerun"
	exit 1
fi
if [ -z "$DEST" ]; then
	echo "Please fill in DEST and rerun"
	exit 1
fi
if [ ! -d "$CRYPT" ]; then
	echo "Please mkdir $CRYPT, chown it to you and rerun"
	exit 1
fi

if [ -n "$1" ]; then
	PASSWORD=$(cat "$1")
else
	echo -n "EncFS password for $SOURCE: "
	stty -echo
	read PASSWORD
	echo
	stty echo
fi
if [ -z "$PASSWORD" ]; then
	echo "No password specified, aborting!"
	exit 1
fi

# The below can be used to translate filenames to the encoded version.
# I've disabled it because of the problems matching patterns, e.g. *.o
# --------------------------------------------------------------------
#
# # There is no -S option to encfsctl to read password from stdin, so use cat as
# # the external program to get the password which will have the same effect.
# EXCLUDE_ENC=$(echo $PASSWORD | encfsctl encode --extpass cat "$SOURCE" $EXCLUDE)
# for x in $EXCLUDE_ENC; do
# 	echo ' - '$x;
# done

setup_encfs()
{
	echo
	echo "SETTING UP REVERSE ENCFS USING 192 BIT AES KEY AND NO FILENAME ENCRYPTION"
	echo "WARNING: BE SURE THAT DESTINATION DOES NOT ALREADY CONTAIN AN RDIFF BACKUP!"
	echo
	echo "$SOURCE -> $DEST"
	echo "Temporary encfs mountpoint: $CRYPT"
	echo "Optional rsync style filter file: $FILTER"
	echo
	echo -n "10.."; sleep 1
	echo -n "9..."; sleep 1
	echo -n "8..."; sleep 1
	echo -n "7..."; sleep 1
	echo -n "6..."; sleep 1
	echo -n "5..."; sleep 1
	echo -n "4..."; sleep 1
	echo -n "3..."; sleep 1
	echo -n "2..."; sleep 1
	echo "1..."; sleep 1
	# Could do this as an expect script. Answers are:
	# x: Expert
	# 1: AES
	# 192 bits
	# '': default block size
	# 2: Null filename encryption,
	# Password
	ionice -c 3 encfs -S --reverse "$SOURCE" "$CRYPT" << EOF
x
1
192

2
$PASSWORD
EOF
}

mount_encfs()
{
	echo "$PASSWORD" | ionice -c 3 encfs -S --reverse "$SOURCE" "$CRYPT"
}

if [ ! -f "$ENCFS_XML_SRC" ]; then
	setup_encfs || exit 1
else
	mount_encfs || exit 1
fi

if [ -n "$FILTER" ]; then
	nice ionice -c 3 rdiff-backup -v5 --print-statistics --include-globbing-filelist "$FILTER" "$CRYPT/" "$DEST/"
else
	nice ionice -c 3 rdiff-backup -v5 --print-statistics "$CRYPT/" "$DEST/"
fi

fusermount -u "$CRYPT"

echo "Backing up $ENCFS_XML_SRC..."
rsync -avP "$ENCFS_XML_SRC" "$ENCFS_XML_DEST"

if [ -z "$REMOVE" ]; then
	echo "Deleting old incrementals..."
	rdiff-backup --remove-older-than "$REMOVE" "$DEST/"
fi
