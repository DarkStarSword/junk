#include <sys/types.h>
#include <sys/stat.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <stdio.h>

/*
 * Read an entire file into an array and add a NULL terminator.
 *
 * On success a pointer to the allocated array will be returned and the file
 * size will be stored in lenp if given. Returns NULL on failure.
 *
 * NOTE: Array is dynamically allocated and must be freed by the caller.
 */
char * read_file(const char *path, const int flags, int *lenp)
{
	const int BUF_LEN = 512;

	int bytes, idx, fd, read_len;
	char *buf = NULL;

	fd = open(path, flags);
	if (fd < 0)
		goto err;

	buf = malloc(BUF_LEN);
	if (!buf)
		goto err;

	for (idx = 0, bytes = 0, read_len = BUF_LEN;
	     (bytes = read(fd, &buf[idx], read_len)) > 0;
	     idx += bytes, read_len = BUF_LEN - (bytes%BUF_LEN)) {
		if (bytes == BUF_LEN) {
			buf = realloc(buf, idx + 2*BUF_LEN);
			if (!buf)
				goto err_cleanup;
		}
	}
	if (bytes < 0)
		goto err_cleanup;

	buf = realloc(buf, idx+1);
	if (!buf) /* Only shrinking, should not fail */
		goto err_cleanup;
	buf[idx] = 0;
	if (lenp)
		*lenp = idx;

	close(fd);
	return buf;

err_cleanup:
	free(buf);
	close(fd);
err:
	perror("read_file");
	return NULL;
}
