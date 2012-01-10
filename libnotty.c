#include <stdio.h>
#include <dlfcn.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

typedef int (*open_t)(const char *pathname, int flags);
open_t libc_open;
open_t libc_open64;

static void notty_init()
{
	void *libc;
	char *error;

	/* FIXME: Hack for Debian multiarch */
	libc = dlopen("/lib/i386-linux-gnu/i686/cmov/libc.so.6", RTLD_LAZY);

	if (!libc) {
		fputs(dlerror(), stderr);
		exit(1);
	}

	libc_open = dlsym(libc, "open");
	if ((error = dlerror()) != NULL) {
		fprintf(stderr, "%s\n", error);
		exit(1);
	}

	libc_open64 = dlsym(libc, "open64");
	if ((error = dlerror()) != NULL) {
		fprintf(stderr, "%s\n", error);
		exit(1);
	}
}

int open(const char *pathname, int flags)
{
	if (!strcmp(pathname, "/dev/tty")) {
		fprintf(stderr, "INTERCEPTED open(%s, %#x)\n", pathname, flags);
		errno = EINVAL;
		return -1;
	}

	if (!libc_open)
		notty_init();

	return libc_open(pathname, flags);
}

int open64(const char *pathname, int flags)
{
	if (!strcmp(pathname, "/dev/tty")) {
		fprintf(stderr, "INTERCEPTED open64(%s, %#x)\n", pathname, flags);
		errno = EINVAL;
		return -1;
	}

	if (!libc_open64)
		notty_init();

	return libc_open64(pathname, flags);
}
