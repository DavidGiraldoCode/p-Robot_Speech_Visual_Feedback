/* 
* Oct 22 / 2025
* This program controls an LED array from an input data stream from the Serial port. 
* A Java Processing program sends integers [0, 255], and the Arduino takes care of it.
* https://github.com/DavidGiraldoCode/s-Arduino_Audio_Wave_Vizualization_for_Conversational_Robots.git
*
*/

#include "libs/pitches.h"
//#define     ARRAY_SIZE 6 // Not type sae
constexpr uint8_t         ARRAY_SIZE        = 6;
constexpr unsigned long   BAUD_RATE         = 9600;

const     uint8_t   LED_ARRAY[ARRAY_SIZE]   = {3,5,6,9,10,11};
const     uint8_t   BTN_PIN                 = 2;
const     uint8_t   PIEZO_BUZZ_PIN          = 7;
const     uint8_t   led_count               = ARRAY_SIZE;
const     unsigned int TALKING_STATE        = 255;
const     unsigned int BASE_STATE           = 25;
const     unsigned int LISTENING_STATE      = 10;
          
unsigned  int       turn_on_counter         = 0;
          
          char      furhat_state            = '0';        // Data received from the serial port

// Controlling turn On and Off
constexpr uint8_t   BOUNCE_DELAY            = 10; // milliseconds
unsigned  long      last_debounce_time      = 0;
          bool      is_on                   = false;
          bool      last_system_state       = false;
          uint8_t   btn_state               = 0;
          uint8_t   btn_last_state          = LOW;

// Debounce refers to a technique used in electronics and programming to eliminate false readings caused by the mechanical behavior of physical switches and buttons.
////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////
// PacMan melody, code and headerfiles from https://github.com/hibit-dev/buzzer/tree/master
const   int   melody[] = {
   NOTE_B4, NOTE_B5, NOTE_FS5, NOTE_DS5,
  // NOTE_B5, NOTE_FS5, NOTE_DS5, NOTE_C5,
  // NOTE_C6, NOTE_G6, NOTE_E6, NOTE_C6, NOTE_G6, NOTE_E6,
  
  // NOTE_B4, NOTE_B5, NOTE_FS5, NOTE_DS5, NOTE_B5,
  // NOTE_FS5, NOTE_DS5, NOTE_DS5, NOTE_E5, NOTE_F5,
  //NOTE_F5, NOTE_FS5, NOTE_G5, NOTE_G5, NOTE_GS5, NOTE_A5, NOTE_B5
};

const   int   durations[] = {
   16, 16, 16, 16,
  // 32, 16, 8, 16,
  // 16, 16, 16, 32, 16, 8,
  
  // 16, 16, 16, 16, 32,
  // 16, 8, 32, 32, 32,
  //32, 32, 32, 32, 32, 16, 8
};
////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////


void setup()
{
  pinMode(BTN_PIN, INPUT);
  pinMode(PIEZO_BUZZ_PIN, OUTPUT); //PIEZO_BUZZ_PIN

  for(size_t i = 0; i < 6; i++)
  {
    pinMode(LED_ARRAY[i], OUTPUT);
  }

  for(size_t i = 0; i < led_count * 2; i++)
  {
    digitalWrite(LED_ARRAY[i % led_count], HIGH);
    delay(50);
    digitalWrite(LED_ARRAY[i % led_count], LOW);
    delay(50);
  }

  controllLedArray(0);
  Serial.begin(BAUD_RATE);
}

void controllLedArray(const unsigned int brightness)
{
  for(size_t i = 0; i < led_count; i++)
  {
    analogWrite(LED_ARRAY[i], brightness);
  }
}

void toogleSystem(uint8_t state)
{
  Serial.flush();
  btn_state = state;

  if(btn_state != btn_last_state)
  {
    last_debounce_time = millis();
    last_system_state = is_on;
  }

  if((millis() - last_debounce_time) > BOUNCE_DELAY)
  {
      if( btn_state == HIGH)
        {

          if(last_system_state == false)
            is_on = true;
          else
            is_on = false;

          controllLedArray(is_on ? LISTENING_STATE : LOW);
          soundFeedBack();
        }
  }

  btn_last_state = btn_state;
    
}

void changeLedBaseOnSerialMessages()
{
  while (Serial.available())          // If data is available to read,
  {            
    furhat_state = Serial.read();     // read it and store it in val
  }

  // Silence is indicated by byte value 0
  if (furhat_state == 0)
  {
    controllLedArray(LISTENING_STATE);
  }
  else
  {
    // Clamp to BASE_STATE minimum for visible LED response
    controllLedArray(furhat_state < BASE_STATE ? BASE_STATE : furhat_state);
  }
  
  delay(100);
}

void pacmanTheme()
{
  // CODE and headerfiles from https://github.com/hibit-dev/buzzer/tree/master
  int size = sizeof(durations) / sizeof(int);

  for (int note = 0; note < size; note++) {
    //to calculate the note duration, take one second divided by the note type.
    //e.g. quarter note = 1000 / 4, eighth note = 1000/8, etc.
    int duration = 1200 / durations[note];
    tone(PIEZO_BUZZ_PIN, melody[note], duration);

    //to distinguish the notes, set a minimum time between them.
    //the note's duration + 30% seems to work well:
    int pauseBetweenNotes = duration * 1.30;
    delay(pauseBetweenNotes);
    
    //stop the tone playing:
    noTone(PIEZO_BUZZ_PIN);
  }
}

void soundFeedBack()
{
  if(!last_system_state)
  {
    pacmanTheme();
    // tone(PIEZO_BUZZ_PIN, 440);
    // delay(100);
    // tone(PIEZO_BUZZ_PIN, 494);
    // delay(100);
    // tone(PIEZO_BUZZ_PIN, 523);
    // delay(100);
    // tone(PIEZO_BUZZ_PIN, 587);
    // delay(100);
    // tone(PIEZO_BUZZ_PIN, 659);
    // delay(100);
    // tone(PIEZO_BUZZ_PIN, 698);
    // delay(100);
    // tone(PIEZO_BUZZ_PIN, 784);
    // delay(100);
    // noTone(PIEZO_BUZZ_PIN);
  }
  else
  {
    tone(PIEZO_BUZZ_PIN, 500);
    delay(100);
    tone(PIEZO_BUZZ_PIN, 1500);
    delay(400);
    noTone(PIEZO_BUZZ_PIN);
  }

}

void loop()
{
  toogleSystem(digitalRead(BTN_PIN)); 

  if(!is_on)
      return;
  else
    changeLedBaseOnSerialMessages();

}
