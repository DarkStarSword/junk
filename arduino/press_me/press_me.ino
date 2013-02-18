#include <LiquidCrystal.h>

LiquidCrystal lcd(12,10,5,4,3,2);
const int buttonPin = 1;
const int rLed = 13;
const int buzzPin = 8;


void setup()
{
  lcd.begin(16, 2);
  lcd.noCursor();
  
  pinMode(rLed, OUTPUT);
  pinMode(buttonPin, INPUT);
  pinMode(buzzPin, OUTPUT);
  digitalWrite(rLed, LOW);
}

void disp_press_me()
{
  static int phase = 0;
  
  lcd.clear();
  if (phase % 2 == 0)
    lcd.print("  Press me  --->");
  else
    lcd.print("  Press me  ===>");

  if (phase++ % 10 == 9) {
    lcd.setCursor(5,1);
    lcd.print("Do it!");
  }
}

void click()
{
  digitalWrite(buzzPin, HIGH);
  delayMicroseconds(15);
  digitalWrite(buzzPin, LOW);
}

void kbd(char *str)
{
  return;
  Keyboard.print(str);
}

void tickle()
{
  lcd.clear();
  lcd.setCursor(6,0);
  lcd.print("Ooh!");
  lcd.setCursor(2,1);
  lcd.print("That tickles!");
  
  kbd("\n");
  for (int i = 0; i < 50; i++) {
    kbd("ooh ");
    Mouse.move(+100, -100, 0);
    digitalWrite(rLed, HIGH);
    click();    
    delay(100);
    
    kbd("aah ");
    Mouse.move(-100, +100, 0);
    digitalWrite(rLed, LOW);
    click();
    delay(100);
  }
  kbd("\nThat tickles!");
  disp_press_me();
}

void loop()
{
  static int timer = 0;
  
  int buttonState = digitalRead(buttonPin);
  
  if (buttonState)
    tickle();
  else if (timer == 0)
    disp_press_me();
  
  delay(50);
  ++timer %= 20;
}
