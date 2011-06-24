#ifndef _UTIL_H
#define _UTIL_H

typedef unsigned char u8;
typedef unsigned int u32;
typedef unsigned long long u64;

/* 8MB should be future proof for at least a couple of years...  */
#define DEFAULT_BLOCK_SIZE 8*1024*1024

void showstatus(u64 pos);

struct showstatus_state
{
	u64 last_usec;
	u64 last_pos;
};

void showstatus_init(struct showstatus_state *stat, u64 pos);
void showstatus_timed(u64 pos, struct showstatus_state *stat, char *msg);

unsigned int sd_erase_size(char *filename);

#endif
