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
	if (!buf) {
		perror("malloc");
		exit(1);
	}
	return;
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
	alloc_bufs(sd_erase_size(filename)); /* BLOCK_SIZE set here */
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
