#include <stdio.h>
#include <sys/time.h>
#include <libgen.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <string.h>
#include <unistd.h>

#include "util.h"

void showstatus(u64 pos)
{
	printf("%#.8llx...\r", pos);
}

void showstatus_init(struct showstatus_state *stat, u64 pos)
{
	struct timeval tv;

	gettimeofday(&tv, NULL);
	stat->last_usec = tv.tv_sec*1000000 + tv.tv_usec;
	stat->last_pos = pos;
}

void showstatus_timed(u64 pos, struct showstatus_state *stat, char *msg)
{
	struct timeval tv;
	u64 usec, delta, bytes;
	double rate;
	char *units = "B";

	gettimeofday(&tv, NULL);
	usec = tv.tv_sec*1000000 + tv.tv_usec;
	delta = usec - stat->last_usec;

	if (delta >= 1000000) {
		bytes = pos - stat->last_pos;
		rate = (double)bytes / ((double)delta/1000000.0);
		if (rate >= 1024) {
			rate /= 1024.0;
			units = "KB";
		}
		if (rate >= 1024) {
			rate /= 1024.0;
			units = "MB";
		}
		printf("%s%#.8llx @ %f %s/Sec...\n", msg, pos, rate, units);

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
