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

typedef unsigned char u8;
typedef unsigned long long u64;

#define BLOCK_SIZE 4096
u8 buf[BLOCK_SIZE];

static void showstatus(u64 pos)
{
	printf("%#.8llx...\r", pos);
}

struct showstatus_state
{
	u64 last_usec;
	u64 last_pos;
};

static void showstatus_init(struct showstatus_state *stat)
{
	struct timeval tv;

	gettimeofday(&tv, NULL);
	stat->last_usec = tv.tv_sec*1000000 + tv.tv_usec;
	stat->last_pos = 0;
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

u64 writedata(char *file, unsigned int seed)
{
	int fp = open(file, O_WRONLY | O_LARGEFILE | O_CREAT, S_IWUSR|S_IRUSR);
	u64 pos = 0;
	ssize_t count;

	struct showstatus_state stat;
	showstatus_init(&stat);

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
	return pos;
}

int main(int argc, char *argv[])
{
	unsigned int seed = 0xDEBAC1E;
	u64 written;
	char *filename;

	if (argc < 2) {
		printf("Usage: %s device\nWARNING - all data on device will be destroyed!\n", argv[0]);
		return 1;
	}
	filename = argv[1];

	memset(&buf, 0xff, BLOCK_SIZE);

	written = writedata(argv[1], seed);
	printf("\x1b[36m%llu bytes written to %s.\x1b[0m\n", written, filename);

	sync();

	return 0;
}
