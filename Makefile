all: sdtest dev_one

sdtest: sdtest.c
	gcc -o sdtest sdtest.c -Wall

dev_one: dev_one.c
	gcc -o dev_one dev_one.c -Wall

clean:
	rm -f sdtest dev_one
