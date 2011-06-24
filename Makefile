all: sdtest dev_one

sdtest: sdtest.c util.c
	gcc -o sdtest sdtest.c util.c -Wall

dev_one: dev_one.c util.c
	gcc -o dev_one dev_one.c util.c -Wall

clean:
	rm -f sdtest dev_one
