all: sdtest

sdtest: sdtest.c
	gcc -o sdtest sdtest.c -Wall
