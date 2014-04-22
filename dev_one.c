/*
vi:noexpandtab:ts=2:sw=2
*/

#define _LARGEFILE64_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>
#include <string.h>

#include "util.h"

unsigned int BLOCK_SIZE = 0;
u8 *buf;
u8 *buf_r;


u64 writedata(char *file, u64 start, int read_before_write)
{
	u64 pos = start;
	u64 size = dev_size(file);
	ssize_t count;
	int mode;
	int fp;

	if (read_before_write)
		mode = O_RDWR;
	else
		mode = O_WRONLY;
	fp = open(file, mode | O_LARGEFILE | O_CREAT | O_SYNC, S_IWUSR|S_IRUSR);

	struct showstatus_state stat;
	showstatus_init(&stat, pos, size);

	if (pos) {
		if (lseek64(fp, pos, SEEK_SET) != pos) {
			perror("[1;31mFailed to lseek64[0m");
			return 0;
		}
	}

	while (!size || pos < size) {
		if (!size || size - pos >= BLOCK_SIZE) {
			if (read_before_write) {
				count = read(fp, buf_r, BLOCK_SIZE);
				if (memcmp(buf, buf_r, count)) {
					if (lseek64(fp, pos, SEEK_SET) != pos) {
						perror("[1;31mFailed to lseek64[0m");
						return 0;
					}
					count = write(fp, buf, count);
					stat.written += count;
				}
			} else
				count = write(fp, buf, BLOCK_SIZE);
		} else
			count = write(fp, buf, size - pos);
		if (count == -1) {
			if (errno != ENOSPC)
				perror("write");
			goto out;
		}
		pos += count;

		showstatus_timed(pos, &stat, "");
	}

out:
	showstatus(pos);
	printf("\n");
	fsync(fp);
	close(fp);
	return pos-start;
}

void alloc_bufs(unsigned int size) {
	BLOCK_SIZE = size;
	buf = malloc(BLOCK_SIZE);
	buf_r = malloc(BLOCK_SIZE);
	if (!buf || !buf_r) {
		perror("malloc");
		exit(1);
	}
	return;
}

int main(int argc, char *argv[])
{
	u64 written, start = 0;
	double start_human;
	char *start_units;
	char *filename;
	int read_before_write;

	if (argc < 2 || argc > 4) {
		printf("Usage: %s device [ [ start ] read_before_write ]\nWARNING - all data on device will be destroyed!\n", argv[0]);
		return 1;
	}
	filename = argv[1];
	alloc_bufs(sd_erase_size(filename)); /* BLOCK_SIZE set here */
	if (argc > 2) {
		start = interpret_number(argv[2]);
		start = start - start % BLOCK_SIZE;
	}
	start_human = human_size(start, &start_units);
	printf("Starting at %#llx (%.2f %s)\n", start, start_human, start_units);
	read_before_write = argc > 3;

	memset(buf, 0xff, BLOCK_SIZE);

	written = writedata(argv[1], start, read_before_write);
	printf("\x1b[36m%llu bytes written to %s.\x1b[0m\n", written, filename);

	sync();

	return 0;
}
