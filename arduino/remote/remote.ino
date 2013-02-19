#include <VirtualWire.h>

#define RX_PIN 8 /* Default is 11, but conflicts with piezzo */
#define TX_PIN 12 /* Default is 12 */
#define IR_PIN 7
#define RESET_PIN 6 /* Wired up to RST to allow software reset */

/* Leostick peripherals */
#define RED_PIN 13
#define GREEN_PIN 9
#define BLUE_PIN 10
#define PIEZO_PIN 11

#undef TX_ATTACHED_DIRECTLY
#ifdef TX_ATTACHED_DIRECTLY
#define TX_PWR 6
#define TX_DAT 5
#define TX_GND 4
#define TX_ANT 3
#define TX_PIN TX_DAT
#endif

void setup()
{
	pinMode(RESET_PIN, INPUT);

    Serial.begin(115200);
    while (!Serial) { ; }
    Serial.println("setup");

#ifdef TX_ATTACHED_DIRECTLY
    pinMode(TX_PWR, INPUT);
    pinMode(TX_ANT, INPUT);
    pinMode(TX_GND, OUTPUT);
    digitalWrite(TX_GND, LOW);
    pinMode(TX_PWR, OUTPUT);
    digitalWrite(TX_PWR, HIGH);
#endif

#if 1
	/* Something here is setting PIN 10 HIGH */
    vw_set_rx_pin(RX_PIN);
    vw_set_tx_pin(TX_PIN);

    // Initialise the IO and ISR
    vw_set_ptt_inverted(true); // Required for DR3100
    vw_setup(2000);	 // Bits per sec

    vw_rx_start();       // Start the receiver PLL running
#endif

	/* Turn off those damn lights! */
	digitalWrite(RED_PIN, LOW);
	digitalWrite(GREEN_PIN, LOW);
	digitalWrite(BLUE_PIN, LOW);
}

static void transmit_433(unsigned int len, char *code,
			 unsigned int short_delay, /* 700 us */
			 unsigned int long_delay, /* 1400 us */
			 unsigned int transmissions) /* 4 */
{
	int i, j;

	noInterrupts();
	for (i=0; i < transmissions; i++) {
		for (j=0; j < len; j++) {
			digitalWrite(TX_PIN, LOW);
			if (code[j] == '1') {
				/* 1: short delay followed by long pulse */
				delayMicroseconds(short_delay);
				digitalWrite(TX_PIN, HIGH);
				delayMicroseconds(long_delay);
			} else if (code[j] == '0') {
				/* 0: long delay followed by short pulse */
				delayMicroseconds(long_delay);
				digitalWrite(TX_PIN, HIGH);
				delayMicroseconds(short_delay);
			} else {
				Serial.print("WARNING: code[");
				Serial.print(j);
				Serial.print("] not ASCII 0|1: ");
				Serial.println(code[j]);
			}
		}

		digitalWrite(TX_PIN, LOW);
#if 0
		/* Why is this producing zero delay? */
		delay(80);
#else
		/* WTF? An 80ms loop like this only delays for 40ms!
		 * Whatever, Say 160 to get 80ms... */
		for (j = 0; j < 160; j++) {
			delay(1);
		}
#endif
	}
	interrupts();
}

/* FIXME: MERGE WITH ABOVE */
static void transmit_433_heller(unsigned int len, char *code,
			 unsigned int transmissions) /* 4 */
{
	int i, j;

	noInterrupts();
	digitalWrite(TX_PIN, HIGH);
	delayMicroseconds(433);
	digitalWrite(TX_PIN, LOW);

#if 0
	/* XXX: Measure actual delay is correct here */
	/* delayMicroseconds is documented to be inaccurate above ~1.5ms */
	delay(4);
	delayMicroseconds(470);
#else
	for (j = 0; j < 8; j++) {
		delay(1);
	}
#endif

	for (i=0; i < transmissions; i++) {
		for (j=0; j < len; j++) {
			digitalWrite(TX_PIN, HIGH);
			if (code[j] == '1') {
				/* 1: long pulse followed by short delay */
				delayMicroseconds(900);
				digitalWrite(TX_PIN, LOW);
				delayMicroseconds(433);
			} else if (code[j] == '0') {
				/* 0: short pulse followed by long delay */
				delayMicroseconds(450);
				digitalWrite(TX_PIN, LOW);
				delayMicroseconds(883);
			} else {
				Serial.print("WARNING: code[");
				Serial.print(j);
				Serial.print("] not ASCII 0|1: ");
				Serial.println(code[j]);
			}
		}
#if 0
		/* XXX: Measure actual delay is correct here */
		/* delayMicroseconds is documented to be inaccurate above ~1.5ms */
		delay(4);
		delayMicroseconds(470);
#else
		for (j = 0; j < 8; j++) {
			delay(1);
		}
#endif
	}
	interrupts();
}

#if 0
long previousMillis = 0;
long interval = 5000;

static void tx_test()
{
    const char *msg = "hello";
    unsigned long currentMillis = millis();

    if(currentMillis - previousMillis > interval) {
	previousMillis = currentMillis;

	digitalWrite(13, true); // Flash a light to show transmitting
#if 1
	tx_test();
#else
	vw_send((uint8_t *)msg, strlen(msg));
	vw_wait_tx(); // Wait until the whole message is gone
#endif
	digitalWrite(13, false);
    }
}

static void receive_433()
{
    uint8_t buf[VW_MAX_MESSAGE_LEN];
    uint8_t buflen = VW_MAX_MESSAGE_LEN;

    if (vw_get_message(buf, &buflen)) // Non-blocking
    {
	int i;

        digitalWrite(13, true); // Flash a light to show received good message
	// Message with a good checksum received, dump it.
	Serial.print("433MHz Got: ");

	for (i = 0; i < buflen; i++)
	{
	    Serial.print(buf[i], HEX);
	    Serial.print(" ");
	}
	Serial.println("");
        digitalWrite(13, false);
    }
}
#endif

void reboot()
{
	/* It seems a bit silly that there is no API to do this - unless I'm
	 * missing something? Otherwise I could branch to the bootloader, but I'd
	 * need to know what address it expects to start executing at, and if it
	 * has any assumptions about the state of the hardware.
	 */
	Serial.println("Rebooting in 3 seconds...");
	delay(3000);
	pinMode(RESET_PIN, OUTPUT);
	digitalWrite(RESET_PIN, LOW);
	Serial.print("Reboot failed, ensure PIN ");
	Serial.print(RESET_PIN);
	Serial.println(" is connected to RST");
}

#define BUF_LEN 64
char buf[BUF_LEN];
int buf_idx = 0;

void loop()
{
	char c;

	if (Serial.available()) {
		c = Serial.read();
		buf[buf_idx++] = c;
		Serial.write(c);
		/* TODO: Handle backspace, etc */
		if (c == '\n' || c == '\r') {
			buf[buf_idx-1] = 0;
			Serial.println("");
			if (!strncasecmp(buf, "reset", 6))
				reboot();
			else if (!strncasecmp(buf, "tx ", 3)) {
				Serial.print("Transmitting ");
				Serial.print(buf_idx-4);
				Serial.println(" bits...");
				transmit_433(buf_idx-4, &buf[3], 700, 1400, 4);
				Serial.println("Done.");
			} else if (!strncasecmp(buf, "test ", 5)) {
				Serial.print("Transmitting Heller code ");
				Serial.print(buf_idx-6);
				Serial.println(" bits...");
				transmit_433_heller(buf_idx-6, &buf[5], 4);
				Serial.println("Done.");
			}
			buf_idx = 0;
		} else if (buf_idx == BUF_LEN) {
			Serial.println("OVERFLOW!\n");
			buf_idx = 0;
		}
	}

#if 0
	tx_test();
	receive_433();
#endif
}

// vi:filetype=c:sw=4:ts=4:noexpandtab
