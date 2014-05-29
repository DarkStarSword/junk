all: sdtest dev_one libnotty.so

sdtest: sdtest.c util.c
	gcc -o sdtest sdtest.c util.c -Wall

dev_one: dev_one.c util.c
	gcc -o dev_one dev_one.c util.c -Wall

libnotty.so: libnotty.c
	gcc -Wall -O2 -fpic -shared -ldl -o libnotty.so libnotty.c

stlcam.deb: $(shell find stlcam)
	echo "Remember - you need to 'chown -R root.root stlcam' first to make sure the ownership is correct"
	dpkg-deb -b -Zgzip stlcam

clean:
	rm -f sdtest dev_one libnotty.so
