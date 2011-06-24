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
#include <assert.h>

typedef unsigned char u8;
typedef unsigned int u32;
typedef unsigned long long u64;

u64 global_error_count = 0;

/* 8MB should be future proof for at least a couple of years...  */
#define DEFAULT_BLOCK_SIZE 8*1024*1024
unsigned int BLOCK_SIZE = 0;
u8 *buf_g; /* Generated */
u8 *buf_f; /* File */
#define RAND_BLOCK_SIZE 4*1024 /* Data is seeded every 4K to be block size agnostic */

void _genranddata(u64 pos, u64 off, unsigned int seed)
{
	unsigned int seed_short = (pos >> 32) ^ (pos & 0xffffffff) ^ seed;
	unsigned int i,j;
	u32 tmp1, tmp2;

	assert(RAND_MAX >= 31); /* Assert that rand() still gives us the amount
				   of random bits we rely on below. */
	assert(RAND_BLOCK_SIZE % 4 == 0);

	srand(seed_short); rand(); rand();

	for (i=0; i < RAND_BLOCK_SIZE;) {
		tmp2 = rand();
		for (j=1; i < RAND_BLOCK_SIZE && j < 32; j++) {
			tmp1 = rand();
			buf_g[off + i++] = (tmp1 & 0x000000ff)      ;
			buf_g[off + i++] = (tmp1 & 0x0000ff00) >>  8;
			buf_g[off + i++] = (tmp1 & 0x00ff0000) >> 16;
			/* We don't quite have 4 bytes of random data in tmp1,
			 * so get the high bit from tmp2: */
			buf_g[off + i++] = ((tmp1 & 0x7f000000) | ((tmp2 << j) & 0x80000000)) >> 24;
		}
	}
}

void genranddata(u64 pos, unsigned int seed)
{
	u64 off;

	assert(pos % RAND_BLOCK_SIZE == 0);
	assert(BLOCK_SIZE % RAND_BLOCK_SIZE == 0);

	for (off=0; off < BLOCK_SIZE; off += RAND_BLOCK_SIZE)
		_genranddata(pos+off, off, seed);
}

static void verifyblock(u64 pos, unsigned int seed, unsigned int size)
{
	unsigned int i;

	genranddata(pos, seed);

	for (i=0;i<size;i++) {
		if (buf_f[i] != buf_g[i]) {
			printf("\x1b[1;31m%#.8llx: MISMATCH: %#.2x != %#.2x\x1b[0m\n", pos+i, buf_f[i], buf_g[i]);
			global_error_count++;
		}
	}
}

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

static void showstatus_timed(u64 pos, struct showstatus_state *stat, char *msg)
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

u64 writedata(char *file, u64 start, unsigned int seed)
{
	int fp = open(file, O_WRONLY | O_LARGEFILE | O_CREAT | O_SYNC, S_IWUSR|S_IRUSR);
	u64 pos = start;
	ssize_t count;
	int blockdone = 0;

	struct showstatus_state stat;
	showstatus_init(&stat, pos);

	if (pos) {
		if (lseek64(fp, pos, SEEK_SET) != pos) {
			perror("[1;31mFailed to lseek64[0m");
			return 0;
		}
	}

	while (1) {
		genranddata(pos, seed);

		blockdone = 0;
		while (blockdone < BLOCK_SIZE) {
			count = write(fp, buf_g+blockdone, BLOCK_SIZE-blockdone);
			if (count == -1) {
				if (errno != ENOSPC) {
					perror("write");
					global_error_count++;
				}
				goto out;
			}
			blockdone += count;
			pos += count;
		}

		showstatus_timed(pos, &stat, "writing ");
	}

out:
	showstatus(pos);
	printf("\n");
	fsync(fp);
	close(fp);
	return pos-start;
}

u64 verifydata(char *file, u64 start, unsigned int seed)
{
	int fp = open(file, O_RDONLY | O_LARGEFILE);
	u64 pos = start, startpos;
	ssize_t count;
	int blockdone = 0;

	struct showstatus_state stat;
	showstatus_init(&stat, pos);

	if (pos) {
		if (lseek64(fp, pos, SEEK_SET) != pos) {
			perror("[1;31mFailed to lseek64[0m");
			return 0;
		}
	}

	while (1) {
		startpos = pos;
		blockdone = 0;
		while (blockdone < BLOCK_SIZE) {
			count = read(fp, buf_f+blockdone, BLOCK_SIZE-blockdone);
			switch (count) {
				case -1:
					perror("read");
					global_error_count++;
					/* Fall through */
				case 0:
					verifyblock(startpos, seed, blockdone);
					goto out;
			}
			blockdone += count;
			pos += count;
		}
		verifyblock(startpos, seed, BLOCK_SIZE);

		showstatus_timed(pos, &stat, "verifying ");
	}

out:
	showstatus(pos);
	printf("\n");
	fsync(fp);
	close(fp);
	return pos-start;
}

void _alloc_bufs(unsigned int size) {
	BLOCK_SIZE = size;
	buf_g = malloc(BLOCK_SIZE);
	buf_f = malloc(BLOCK_SIZE);
	if (!buf_g || !buf_f) {
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
	unsigned int seed = 0xDEBAC1E;
	u64 written, read, start = 0;
	char *filename;
	int readonly;

	if (argc < 2 || argc > 4) {
		printf("Usage: %s device [ start [ readonly ]]\nWARNING - all data on device will be destroyed!\n", argv[0]);
		return 1;
	}
	filename = argv[1];
	alloc_bufs(filename); /* BLOCK_SIZE set here */

	if (argc > 2) {
		sscanf(argv[2], "%llx", &start);
		start = start - start % BLOCK_SIZE;
	}
	printf("Starting at %#llx\n", start);
	readonly = argc > 3;

	if (!readonly) {
		written = writedata(argv[1], start, seed);
		printf("\x1b[36m%llu bytes written to %s, verifying...\x1b[0m\n", written, filename);
	}

	sync();

	read = verifydata(argv[1], start, seed);
	printf("\x1b[36m%llu bytes read from %s.\x1b[0m\n", read, filename);

	if (!readonly && written != read) {
		printf("\x1b[1;31mSIZE MISMATCH: wrote %llu bytes, but read back %llu bytes!\x1b[0m\n", written, read);
		global_error_count++;
	}

	if (global_error_count) {
		printf("\x1b[1;31m\n%llu Errors detected :-(\x1b[0m\n", global_error_count);
		return 1;
	}

	if (read)
		printf("\x1b[1;32m\nNo Errors Detected :-)\x1b[0m\n");
	return 0;
}
