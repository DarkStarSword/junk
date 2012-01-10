all: sdtest dev_one libnotty.so

sdtest: sdtest.c util.c
	gcc -o sdtest sdtest.c util.c -Wall

dev_one: dev_one.c util.c
	gcc -o dev_one dev_one.c util.c -Wall

libnotty.so: libnotty.c
	gcc -Wall -O2 -fpic -shared -ldl -o libnotty.so libnotty.c

clean:
	rm -f sdtest dev_one libnotty.so
