#define _LARGEFILE64_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <fcntl.h>
#include <errno.h>
#include <string.h>
#include <libgen.h>

typedef unsigned char u8;
typedef unsigned long long u64;

/* 8MB should be future proof for at least a couple of years...  */
#define DEFAULT_BLOCK_SIZE 8*1024*1024
unsigned int BLOCK_SIZE = 0;
u8 *buf;

static void showstatus(u64 pos)
{
	printf("%#.8llx...\r", pos);
}

struct showstatus_state
{
	u64 last_usec;
	u64 last_pos;
};

static void showstatus_init(struct showstatus_state *stat, u64 pos)
{
	struct timeval tv;

	gettimeofday(&tv, NULL);
	stat->last_usec = tv.tv_sec*1000000 + tv.tv_usec;
	stat->last_pos = pos;
}

static void showstatus_timed(u64 pos, struct showstatus_state *stat)
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
		printf("%#.8llx @ %f %s/Sec...\n", pos, rate, units);

		stat->last_usec = usec;
		stat->last_pos = pos;
	}
}

u64 writedata(char *file, u64 start)
{
	int fp = open(file, O_WRONLY | O_LARGEFILE | O_CREAT | O_SYNC, S_IWUSR|S_IRUSR);
	u64 pos = start;
	ssize_t count;

	struct showstatus_state stat;
	showstatus_init(&stat, pos);

	if (pos) {
		if (lseek64(fp, pos, SEEK_SET) != pos) {
			perror("[1;31mFailed to lseek64[0m");
			return 0;
		}
	}

	while (1) {
		count = write(fp, buf, BLOCK_SIZE);
		if (count == -1) {
			if (errno != ENOSPC)
				perror("write");
			goto out;
		}
		pos += count;

		showstatus_timed(pos, &stat);
	}

out:
	showstatus(pos);
	printf("\n");
	fsync(fp);
	close(fp);
	return pos - start;
}

void _alloc_bufs(unsigned int size) {
	BLOCK_SIZE = size;
	buf = malloc(BLOCK_SIZE);
	if (!buf) {
		perror("malloc");
		exit(1);
	}
	return;
}

void alloc_bufs(char *filename)
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
	return _alloc_bufs(size);

def_bs_close:
	close(fp);
def_bs:
	printf("\x1b[1;33mNOTE: Could not determine erase block size of %s - assuming %u bytes\x1b[0m\n", devname, DEFAULT_BLOCK_SIZE);
	return _alloc_bufs(DEFAULT_BLOCK_SIZE);
}

int main(int argc, char *argv[])
{
	u64 written, start = 0;
	char *filename;

	if (argc < 2 || argc > 3) {
		printf("Usage: %s device [start]\nWARNING - all data on device will be destroyed!\n", argv[0]);
		return 1;
	}
	filename = argv[1];
	alloc_bufs(filename); /* BLOCK_SIZE set here */
	if (argc > 2) {
		sscanf(argv[2], "%llx", &start);
		start = start - start % BLOCK_SIZE;
	}
	printf("Starting at %#llx\n", start);

	memset(buf, 0xff, BLOCK_SIZE);

	written = writedata(argv[1], start);
	printf("\x1b[36m%llu bytes written to %s.\x1b[0m\n", written, filename);

	sync();

	return 0;
}
