#define LOGIC_GATE_A_PIN 0
#define LOGIC_GATE_B_PIN 1
#define LOGIC_GATE_RESULT_PIN A0
#define LOGIC_GATE_STATUS_00_PIN 7
#define LOGIC_GATE_STATUS_01_PIN 6
#define LOGIC_GATE_STATUS_10_PIN 5
#define LOGIC_GATE_STATUS_11_PIN 4
const uint8_t LOGIC_GATE_STATUS_PINS[] = { /* 1, b, 5, 4 */
  LOGIC_GATE_STATUS_00_PIN,
  LOGIC_GATE_STATUS_01_PIN,
  LOGIC_GATE_STATUS_10_PIN,
  LOGIC_GATE_STATUS_11_PIN,
};
#define TRUTH_TABLE_TEST_PIN 13

#define SHIFT_PIN_SI 2
#define SHIFT_PIN_SCK 3
#define SHIFT_PIN_RCK 3

#define SHIFT_REGISTER 0x20
#define QA (SHIFT_REGISTER | 0)
#define QB (SHIFT_REGISTER | 1)
#define QC (SHIFT_REGISTER | 2)
#define QD (SHIFT_REGISTER | 3)
#define QE (SHIFT_REGISTER | 4)
#define QF (SHIFT_REGISTER | 5)
#define QG (SHIFT_REGISTER | 6)
#define QH (SHIFT_REGISTER | 7)

bool is_shift_pin(int pin)
{
  return (pin & SHIFT_REGISTER);
}

/* Mapping between arduino digital pins and display pins: */
#define DISP_PIN_1      QD
#define DISP_PIN_2      QE
#define DISP_PIN_3      QF
#define DISP_PIN_4      QG
#define DISP_PIN_5      QH
#define DISP_PIN_6_NEG  8
#define DISP_PIN_7      QA
#define DISP_PIN_8_NEG  9
#define DISP_PIN_9_NEG  10
#define DISP_PIN_10     QC
#define DISP_PIN_11     QB
#define DISP_PIN_12_NEG 12

/* Definition of segment/digit pins on LED display */

/* LOW to enable digit */
#define DIG_1  DISP_PIN_12_NEG
#define DIG_2  DISP_PIN_9_NEG
#define DIG_3  DISP_PIN_8_NEG
#define DIG_4  DISP_PIN_6_NEG
const uint8_t POS_PINS[] = {DIG_1, DIG_2, DIG_3, DIG_4};

/*
 * SEGMENTS:
 *
 *   __A__
 *  |     |
 *  F     B
 *  |__G__|
 *  |     |
 *  E     C
 *  |__D__| .DP
 */

/* HIGH to enable segment */
#define SEG_PIN_A  DISP_PIN_11
#define SEG_PIN_B  DISP_PIN_7
#define SEG_PIN_C  DISP_PIN_4
#define SEG_PIN_D  DISP_PIN_2
#define SEG_PIN_E  DISP_PIN_1
#define SEG_PIN_F  DISP_PIN_10
#define SEG_PIN_G  DISP_PIN_5
#define SEG_PIN_DP DISP_PIN_3
const uint8_t SEGMENT_PINS[] = {SEG_PIN_A, SEG_PIN_B, SEG_PIN_C, SEG_PIN_D, SEG_PIN_E, SEG_PIN_F, SEG_PIN_G, SEG_PIN_DP};

#define NUM_DIGITS sizeof(POS_PINS)
#define NUM_SEGS   sizeof(SEGMENT_PINS)


#define SEG_A  1 << 0
#define SEG_B  1 << 1
#define SEG_C  1 << 2
#define SEG_D  1 << 3
#define SEG_E  1 << 4
#define SEG_F  1 << 5
#define SEG_G  1 << 6
#define SEG_DP 1 << 7

typedef uint8_t seg_t;
const seg_t ALL_SEGS = (SEG_A | SEG_B | SEG_C | SEG_D | SEG_E | SEG_F | SEG_G | SEG_DP);
const seg_t BLANK_SEGS = 0;

/* Multiple characters with a common symbols are defined here for convenience */
#define FONT_A (SEG_A | SEG_B | SEG_C | SEG_E | SEG_F | SEG_G)
#define FONT_b (SEG_F | SEG_G | SEG_C | SEG_D | SEG_E)
#define FONT_C (SEG_A | SEG_F | SEG_E | SEG_D) /* C, [, {, ( */
#define FONT_d (SEG_B | SEG_C | SEG_D | SEG_E | SEG_G)
#define FONT_E (SEG_A | SEG_F | SEG_G | SEG_E | SEG_D)
#define FONT_F (SEG_A | SEG_F | SEG_G | SEG_E)
#define FONT_H (SEG_F | SEG_E | SEG_G | SEG_B | SEG_C) /* H, X, x */
#define FONT_I (SEG_F | SEG_E) /* I, l, | */
#define FONT_J (SEG_B | SEG_C | SEG_D | SEG_E)
#define FONT_k (SEG_F | SEG_E | SEG_G | SEG_D)
#define FONT_O (SEG_A | SEG_B | SEG_C | SEG_D | SEG_E | SEG_F) /* 0, o */
#define FONT_P (SEG_E | SEG_F | SEG_A | SEG_B | SEG_G)
#define FONT_q (SEG_A | SEG_F | SEG_G | SEG_B | SEG_C)
#define FONT_r (SEG_E | SEG_G)
#define FONT_S (SEG_A | SEG_F | SEG_G | SEG_C | SEG_D) /* s, S, 5 */
#define FONT_y (SEG_F | SEG_G | SEG_B | SEG_C | SEG_D)
#define FONT_Z (SEG_A | SEG_B | SEG_G | SEG_E | SEG_D) /* z, Z, 2 */
#define FONT_CLOSE_BRACKET (SEG_A | SEG_B | SEG_C | SEG_D) /* ), ], } */
#define FONT_DOT SEG_DP /* . , */

#define ASCII_OFF 0x20 /* Skip the first 32 characters */
/* Font table, starting with ASCII 0x20 */
const seg_t font[] = {
  /* SPACE */ BLANK_SEGS,
  /* ! */ SEG_B | SEG_DP,
  /* " */ SEG_F | SEG_B,
  /* # */ ALL_SEGS,
  /* $ */ 0,
  /* % */ SEG_B | SEG_G | SEG_E | SEG_DP,
  /* & */ SEG_D | SEG_E | SEG_G | SEG_B | SEG_A | SEG_F,
  /* ' */ SEG_F,
  /* ( */ FONT_C,
  /* ) */ FONT_CLOSE_BRACKET,
  /* * */ SEG_A | SEG_B | SEG_G | SEG_F,
  /* + */ SEG_B | SEG_C | SEG_G,
  /* , */ FONT_DOT,
  /* - */ SEG_G,
  /* . */ FONT_DOT,
  /* / */ SEG_E | SEG_G | SEG_B,
  /* 0 */ FONT_O,
  /* 1 */ SEG_B | SEG_C,
  /* 2 */ FONT_Z,
  /* 3 */ SEG_A | SEG_B | SEG_G | SEG_C | SEG_D,
  /* 4 */ SEG_F | SEG_G | SEG_B | SEG_C,
  /* 5 */ FONT_S,
  /* 6 */ SEG_F | SEG_E | SEG_D | SEG_C | SEG_G,
  /* 7 */ SEG_A | SEG_B | SEG_C,
  /* 8 */ SEG_A | SEG_B | SEG_C | SEG_D | SEG_E | SEG_F | SEG_G,
  /* 9 */ SEG_C | SEG_B | SEG_A | SEG_F | SEG_G,
  /* : */ SEG_A | SEG_D,
  /* ; */ SEG_A | SEG_DP,
  /* < */ SEG_A | SEG_F | SEG_G,
  /* = */ SEG_G | SEG_D,
  /* > */ SEG_A | SEG_B | SEG_G,

  /* ? */ SEG_A | SEG_B | SEG_G | SEG_E | SEG_DP,
  /* @ */ SEG_B | SEG_A | SEG_F | SEG_E | SEG_D,
  /* A */ FONT_A,
  /* B */ FONT_b,
  /* C */ FONT_C,
  /* D */ FONT_d,
  /* E */ FONT_E,
  /* F */ FONT_F,
  /* G */ SEG_A | SEG_F | SEG_E | SEG_D | SEG_C,
  /* H */ FONT_H,
  /* I */ FONT_I,
  /* J */ FONT_J,
  /* K */ FONT_k,
  /* L */ SEG_F | SEG_E | SEG_D,
  /* M */ 0,
  /* N */ SEG_E | SEG_F | SEG_A | SEG_B | SEG_C,
  /* O */ FONT_O,
  /* P */ FONT_P,
  /* Q */ FONT_q,
  /* R */ FONT_r,
  /* S */ FONT_S,
  /* T */ SEG_A | SEG_F | SEG_E,
  /* U */ SEG_F | SEG_E | SEG_D | SEG_C | SEG_B,
  /* V */ SEG_F | SEG_E | SEG_D | SEG_B,
  /* W */ 0,
  /* X */ FONT_H,
  /* Y */ FONT_y,
  /* Z */ FONT_Z,
  /* [ */ FONT_C,
  /* \ */ SEG_F | SEG_G | SEG_C,
  /* ] */ FONT_CLOSE_BRACKET,
  /* ^ */ SEG_F | SEG_A | SEG_B,
  /* _ */ SEG_D,

  /* ` */ SEG_B,
  /* a */ FONT_A,
  /* b */ FONT_b,
  /* c */ SEG_G | SEG_E | SEG_D,
  /* d */ FONT_d,
  /* e */ FONT_E,
  /* f */ FONT_F,
  /* g */ SEG_A | SEG_F | SEG_G | SEG_B | SEG_C | SEG_D,
  /* h */ SEG_F | SEG_E | SEG_G | SEG_C,
  /* i */ SEG_E,
  /* j */ FONT_J,
  /* k */ FONT_k,
  /* l */ FONT_I,
  /* m */ 0,
  /* n */ SEG_E | SEG_G | SEG_C,
  /* o */ SEG_G | SEG_C | SEG_D | SEG_E,
  /* p */ FONT_P,
  /* q */ FONT_q,
  /* r */ FONT_r,
  /* s */ FONT_S,
  /* t */ SEG_F | SEG_E | SEG_G,
  /* u */ SEG_E | SEG_D | SEG_C,
  /* v */ SEG_E | SEG_D,
  /* w */ 0,
  /* x */ FONT_H,
  /* y */ FONT_y,
  /* z */ FONT_Z,
  /* { */ FONT_C,
  /* | */ FONT_I,
  /* } */ FONT_CLOSE_BRACKET,
  /* ~ */ /*SEG_A, */
  /* ~ */ SEG_G | SEG_C,
  /* DEL */ 0,
};

void pos_state(int pos, int state)
{
  digitalWrite(POS_PINS[pos], !state);
}

void all_pos_state(int state)
{
  int i;

  for (i = 0; i < NUM_DIGITS; i++)
    digitalWrite(POS_PINS[i], !state);
}

void segs(seg_t segs)
{
  int i, state;
  uint8_t shift = 0;

  /* I could skip this by making SEG_X match the shift register outputs */
  for (i = 0; i < NUM_SEGS; i++) {
    state = ((1<<i) & segs ? HIGH : LOW);
    if (is_shift_pin(SEGMENT_PINS[i]))
      if (state)
        shift |= 1 << (SEGMENT_PINS[i] & ~SHIFT_REGISTER);
    else
      digitalWrite(SEGMENT_PINS[i], state);
  }

  digitalWrite(SHIFT_PIN_SCK, LOW);
  digitalWrite(SHIFT_PIN_RCK, LOW);
  for (i = 0; i < 8; i++) {
    digitalWrite(SHIFT_PIN_SI, (shift & (0x80 >> i) ? HIGH : LOW));
    digitalWrite(SHIFT_PIN_SCK, HIGH);
    digitalWrite(SHIFT_PIN_SCK, LOW);
  }
  digitalWrite(SHIFT_PIN_RCK, HIGH);
  digitalWrite(SHIFT_PIN_RCK, LOW);
}

void pr_array(const seg_t array[NUM_DIGITS])
{
  int i;

  for (i = 0; i < NUM_DIGITS; i++) {
    segs(array[i]);
    pos_state(i, 1);
    delay(4);
    pos_state(i, 0);
  }
}

void pr_text(const seg_t array[NUM_DIGITS])
{
  int i;

  for (i = 0; i < NUM_DIGITS; i++) {
    segs(font[array[i] - ASCII_OFF]);
    pos_state(i, 1);
    delay(4);
    pos_state(i, 0);
  }
}

void num2array(long num, seg_t array[4])
{
  int i, neg = 0, sig = 0;
  
  if (num > 9999 || num < -999) {
    array[0] = 'F';
    array[1] = 'A';
    array[2] = 'I';
    array[3] = 'L';
    return;
  }
  
  if (num < 0) {
    neg = 1;
    num = num * -1;
  }
  array[0] = '0' + (num / 1000) % 10;
  array[1] = '0' + (num /  100) % 10;
  array[2] = '0' + (num /   10) % 10;
  array[3] = '0' + (num /    1) % 10;

  for (i = 0; i < 4; i++) {
    if (!sig && array[i] != '0')
      sig = i+1;
    if (!sig && i < 3 && array[i] == '0')
      array[i] = ' ';
  }
  
  if (neg && sig > 1)
    array[sig-2] = '-';
}

void reset_disp()
{
  int i;

  segs(BLANK_SEGS);

  for (i = 0; i < NUM_SEGS; i++) {
    if (!is_shift_pin(SEGMENT_PINS[i]))
      pinMode(SEGMENT_PINS[i], OUTPUT);
  }
  for (i = 0; i < NUM_DIGITS; i++) {
    pinMode(POS_PINS[i], OUTPUT);
    pos_state(i, 1);
  }
}

/* https://en.wikipedia.org/wiki/Gray_code */
static inline unsigned int bin2gray(unsigned int num)
{
  return (num >> 1) ^ num;
}

static inline unsigned int gray2bin(unsigned int num)
{
  unsigned int numBits = 8 * sizeof(num);
  unsigned int shift;
  for (shift = 1; shift < numBits; shift *= 2)
  {
    num ^= num >> shift;
  }
  return num;
}

seg_t truth_tables[16][NUM_DIGITS];

void init_truth_tables()
{
  unsigned int input, gray, a, b, bit;

  int t_true=0, t_false=0, t_a=0, t_b=0, t_not_a=0, t_not_b=0;
  int t_or=0, t_nor=0, t_and=0, t_nand=0, t_xor=0, t_xnor=0;
  int t_A_and_not_B=0, t_B_and_not_A=0;
  int t_A_or_not_B=0, t_B_or_not_A=0;

  for (input = 0; input < 4; input++) {
    gray = bin2gray(input);
    a = (gray & 0x1 ? 1 : 0);
    b = (gray & 0x2 ? 1 : 0);
    bit = (1 << 3-input);

    t_true        |= (  1       ? bit : 0);
    t_false       |= (  0       ? bit : 0);

    t_a           |= (  a       ? bit : 0);
    t_not_a       |= (! a       ? bit : 0);
    t_b           |= (  b       ? bit : 0);
    t_not_b       |= (! b       ? bit : 0);

    t_or          |= ( (a || b) ? bit : 0);
    t_nor         |= (!(a || b) ? bit : 0);

    t_and         |= ( (a && b) ? bit : 0);
    t_nand        |= (!(a && b) ? bit : 0);

    t_xor         |= ( (a ^  b) ? bit : 0);
    t_xnor        |= (!(a ^  b) ? bit : 0);

    t_A_and_not_B |= ((a && !b) ? bit : 0);
    t_B_and_not_A |= ((b && !a) ? bit : 0);
    t_A_or_not_B  |= ((a || !b) ? bit : 0);
    t_B_or_not_A  |= ((b || !a) ? bit : 0);
  }

  /* FIXME: Lots of strings here consume excess memory, should only put these
   * in RAM when they are used */
  memcpy(&truth_tables[t_true       ], "TRUE", NUM_DIGITS);
  memcpy(&truth_tables[t_false      ], "FALS", NUM_DIGITS);

  memcpy(&truth_tables[t_a          ], "  A ", NUM_DIGITS);
  memcpy(&truth_tables[t_not_a      ], " ~A ", NUM_DIGITS);
  memcpy(&truth_tables[t_b          ], "  B ", NUM_DIGITS);
  memcpy(&truth_tables[t_not_b      ], " ~B ", NUM_DIGITS);

  memcpy(&truth_tables[t_or         ], " OR ", NUM_DIGITS);
  memcpy(&truth_tables[t_nor        ], "NOR ", NUM_DIGITS);

  memcpy(&truth_tables[t_and        ], " AND", NUM_DIGITS);
  memcpy(&truth_tables[t_nand       ], "NAND", NUM_DIGITS);

  memcpy(&truth_tables[t_xor        ], " XOR", NUM_DIGITS);
  memcpy(&truth_tables[t_xnor       ], "XNOR", NUM_DIGITS);

  memcpy(&truth_tables[t_A_and_not_B], "A^~B", NUM_DIGITS);
  memcpy(&truth_tables[t_B_and_not_A], "B^~A", NUM_DIGITS);
  memcpy(&truth_tables[t_A_or_not_B ], "Au~B", NUM_DIGITS);
  memcpy(&truth_tables[t_B_or_not_A ], "Bu~A", NUM_DIGITS);
}

void setup()
{
  int i;

  reset_disp();

  pinMode(SHIFT_PIN_SI, OUTPUT);
  digitalWrite(SHIFT_PIN_SI, LOW);
  pinMode(SHIFT_PIN_SCK, OUTPUT);
  digitalWrite(SHIFT_PIN_SCK, LOW);
  pinMode(SHIFT_PIN_RCK, OUTPUT);
  digitalWrite(SHIFT_PIN_RCK, LOW);

  pinMode(LOGIC_GATE_A_PIN, OUTPUT);
  digitalWrite(LOGIC_GATE_A_PIN, LOW);
  pinMode(LOGIC_GATE_B_PIN, OUTPUT);
  digitalWrite(LOGIC_GATE_B_PIN, LOW);
  pinMode(LOGIC_GATE_RESULT_PIN, INPUT);

  pinMode(LOGIC_GATE_STATUS_00_PIN, OUTPUT);
  digitalWrite(LOGIC_GATE_STATUS_00_PIN, LOW);
  pinMode(LOGIC_GATE_STATUS_01_PIN, OUTPUT);
  digitalWrite(LOGIC_GATE_STATUS_01_PIN, LOW);
  pinMode(LOGIC_GATE_STATUS_10_PIN, OUTPUT);
  digitalWrite(LOGIC_GATE_STATUS_10_PIN, LOW);
  pinMode(LOGIC_GATE_STATUS_11_PIN, OUTPUT);
  digitalWrite(LOGIC_GATE_STATUS_11_PIN, LOW);

  pinMode(TRUTH_TABLE_TEST_PIN, INPUT);
  digitalWrite(TRUTH_TABLE_TEST_PIN, HIGH);

  init_truth_tables();
}

void logic_gate_test()
{
  unsigned int input, gray, a, b, r, bit, t = 0;

  for (input = 0; input < 4; input++) {
    gray = bin2gray(input);
    a = (gray & 0x1 ? HIGH : LOW);
    b = (gray & 0x2 ? HIGH : LOW);
    bit = (1 << 3-input);

    digitalWrite(LOGIC_GATE_A_PIN, a);
    digitalWrite(LOGIC_GATE_B_PIN, b);
    delay(1);

    r = digitalRead(LOGIC_GATE_RESULT_PIN);
    digitalWrite(LOGIC_GATE_STATUS_PINS[input], r);

    t |= (r ? bit : 0);
  }
  digitalWrite(LOGIC_GATE_A_PIN, LOW);
  digitalWrite(LOGIC_GATE_B_PIN, LOW);

  pr_text(truth_tables[t]);
}

void truth_table_test()
{
  int i, s;
  unsigned long m;

#if 1
  for (s = 0; s < 4; s++)
    digitalWrite(LOGIC_GATE_STATUS_PINS[s], LOW);
  m = millis();
  while (millis() - m < 1000)
    pr_text((seg_t*)"TEST");
#endif

  for (i = 0; i < 16; i++) {
    for (s = 0; s < 4; s++)
      digitalWrite(LOGIC_GATE_STATUS_PINS[s], (i & (1 << (3-s)) ? HIGH : LOW));
    m = millis();
    while (millis() - m < 1000)
      pr_text(truth_tables[i]);
  }

  for (s = 0; s < 4; s++)
    digitalWrite(LOGIC_GATE_STATUS_PINS[s], LOW);
  m = millis();
  while (millis() - m < 1000) {
#if 0
    /* The "DONE" string here apparently is enough to push the memory usage over
     * the edge and corrupt POS_PIN[4]. Either that or adding this moves memory
     * around enough to corrupt it instead of something else benign.
     */
    pr_text((seg_t*)"DONE");
#endif
  }
}

void loop()
{
  if (digitalRead(TRUTH_TABLE_TEST_PIN) == LOW)
    truth_table_test();
  else
    logic_gate_test();
}

// vim:filetype=c:sw=2:ts=2:expandtab
