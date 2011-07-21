/*
vi:noexpandtab:ts=2:sw=2
*/

#define _LARGEFILE64_SOURCE

#include <stdio.h>
#include <sys/time.h>
#include <libgen.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <string.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <linux/fs.h>
#include <regex.h>
#include <stdlib.h>

#include "util.h"

static char *human_sizes[] = {"B", "KB", "MB", "GB", "TB"};
static int human_sizes_len = 5;

static double human_size(double size, char **units)
{
	int idx = 0;

	for (; size >= 1024.0 && idx < human_sizes_len; idx++, size /= 1024.0);

	*units = human_sizes[idx];
	return size;
}

/*
 * Note: Does not handle negatives or floating point numbers.
 *
 * The exception is filesizes where (e.g.) 3.2GB will be translated into
 * integer bytes.
 */
u64 interpret_number(char *string)
{
	int rc;
	u64 ret;
	regex_t preg;
	const int nmatch = 8;
	regmatch_t pmatch[nmatch];
	double val;

	/* Filesize */
	rc = regcomp(&preg, "^([1-9][0-9]*(.[0-9]+)?|0(.[0-9]+)?) ?(B|KB|MB|GB|TB)$", REG_EXTENDED);
	/* Match groups:
	 * 0: Entire string
	 * 1: Numeric value
	 * 2/3: Ignore (Indicates value is floating point)
	 * 4: Units
	 */
	if (rc)
		goto err;
	rc = regexec(&preg, string, nmatch, pmatch, 0);
	regfree(&preg);
	if (!rc) {
		u64 mult = 1;
		switch (string[pmatch[4].rm_so]) {
			/* Exploit the C fall-through goodness */
			case 'T': mult *= 1024;
			case 'G': mult *= 1024;
			case 'M': mult *= 1024;
			case 'K': mult *= 1024;
			case 'B': break;
			default:
				printf("ERR: Unrecognised filesize unit\n");
		}

		/* Add null terminator after numeric value */
		string[pmatch[1].rm_eo] = 0;

		sscanf(string, "%lf", &val);
		return val * mult;
	}

	/* Hex */
	rc = regcomp(&preg, "^0x[0-9a-fA-F]+$", REG_EXTENDED);
	if (rc)
		goto err;
	rc = regexec(&preg, string, nmatch, pmatch, 0);
	regfree(&preg);
	if (!rc) {
		sscanf(string, "%llx", &ret);
		return ret;
	}

	/* Octal */
	rc = regcomp(&preg, "^0[0-7]+$", REG_EXTENDED);
	if (rc)
		goto err;
	rc = regexec(&preg, string, nmatch, pmatch, 0);
	regfree(&preg);
	if (!rc) {
		sscanf(string, "%llo", &ret);
		return ret;
	}

	/* Decimal */
	rc = regcomp(&preg, "^([1-9][0-9]*|0)$", REG_EXTENDED);
	if (rc)
		goto err;
	rc = regexec(&preg, string, nmatch, pmatch, 0);
	regfree(&preg);
	if (!rc) {
		sscanf(string, "%llu", &ret);
		return ret;
	}

	return 0;

err:
	{
		int errbuf_size;
		char *errbuf;

		errbuf_size = regerror(rc, &preg, NULL, 0);
		errbuf = malloc(errbuf_size);
		regerror(rc, &preg, errbuf, errbuf_size);
		printf("regex error: %s\n", errbuf);
		free(errbuf);
		return 0;
	}
}

u64 dev_size(char *filename)
{
	struct stat st;
	u64 ret = 0;
	int fd = open(filename, O_RDONLY | O_LARGEFILE);
	if (fd == -1)
		return 0;

	fstat(fd, &st);
	if (st.st_size) {
		ret = st.st_size;
		goto out;
	}

	/* FIXME: Make sure this is a block device */
	ioctl(fd, BLKGETSIZE64, &ret);

out:
	close(fd);
	return ret;
}

void showstatus(u64 pos)
{
	printf("%#.8llx...\r", pos);
}

void showstatus_init(struct showstatus_state *stat, u64 pos, u64 size)
{
	struct timeval tv;

	gettimeofday(&tv, NULL);
	stat->last_usec = tv.tv_sec*1000000 + tv.tv_usec;
	stat->last_pos = pos;
	stat->size = size;
	stat->size_human = human_size(size, &stat->size_units);
}

void showstatus_timed(u64 pos, struct showstatus_state *stat, char *msg)
{
	struct timeval tv;
	u64 usec, delta, bytes;
	double rate;
	char *units, *pos_units;
	double hpos = (human_size(pos, &pos_units));

	gettimeofday(&tv, NULL);
	usec = tv.tv_sec*1000000 + tv.tv_usec;
	delta = usec - stat->last_usec;

	if (delta >= 1000000) {
		bytes = pos - stat->last_pos;
		rate = human_size((double)bytes / ((double)delta/1000000.0), &units);
		if (stat->size) {
			printf("%s%#.8llx (%.2f %s / %.2f %s %.2f%%) @ %f %s/Sec...\n", msg, pos,
					   hpos, pos_units,
					   stat->size_human, stat->size_units,
					   (double)pos / stat->size * 100.0,
					   rate, units);
		} else {
			printf("%s%#.8llx (%.2f %s) @ %f %s/Sec...\n", msg, pos,
					   hpos, pos_units, rate, units);
		}
		stat->last_usec = usec;
		stat->last_pos = pos;
	}
}

unsigned int sd_erase_size(char *filename)
{
	char *devname;
	char sys_fn[256];
	int fp;
	char tmp[64];
	unsigned int size;

	/* If it is an SD card, try to determine the erase block size */
	devname = basename(filename);
	if (snprintf(sys_fn, 256, "/sys/class/block/%s/device/preferred_erase_size", devname) < 0)
		goto def_bs;

	fp = open(sys_fn, O_RDONLY);
	if (fp < 0)
		goto def_bs;

	memset(tmp, 0, 64);
	/* Assume this call will not be interrupted */
	if (read(fp, tmp, 64) <= 0)
		goto def_bs_close;

	/* Potential overflow if 64 chars read and lacking NULL terminator */
	if (sscanf(tmp, "%u", &size) != 1)
		goto def_bs_close;

	close(fp);

	printf("\x1b[36mUsing erase size of %u bytes\x1b[0m\n", size);
	return size;

def_bs_close:
	close(fp);
def_bs:
	printf("\x1b[1;33mNOTE: Could not determine erase block size of %s - assuming %u bytes\x1b[0m\n", devname, DEFAULT_BLOCK_SIZE);
	return DEFAULT_BLOCK_SIZE;
}
