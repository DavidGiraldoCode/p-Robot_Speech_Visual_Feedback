/* 
* Oct 24 / 2025
* This program controls an LED array from an input data stream from the Serial port. 
* A Java Processing program sends integers [0, 255], and the Arduino takes care of it.
* https://github.com/DavidGiraldoCode/s-Arduino_Audio_Wave_Vizualization_for_Conversational_Robots.git
*
*/

#include <Adafruit_NeoPixel.h>

#define LED_PIN     6          // Data pin for the NeoPixel ring
#define NUM_PIXELS  16         // Number of LEDs in the ring

Adafruit_NeoPixel ring(NUM_PIXELS, LED_PIN, NEO_GRB + NEO_KHZ800);
uint8_t brightness;

constexpr unsigned long   BAUD_RATE         = 9600;

const     uint8_t   BTN_PIN                 = 2;
const     unsigned int TALKING_STATE        = 255;
const     unsigned int BASE_STATE           = 15;
const     unsigned int LISTENING_STATE      = 5;
          
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


void setup()
{
  pinMode(BTN_PIN, INPUT);

  ring.begin();
  ring.setBrightness(0);
  ring.show();

  Serial.begin(BAUD_RATE);
}

void controllNeoPixel(const unsigned int brightness)
{
  
  ring.setBrightness(brightness);
  for (int i = 0; i < NUM_PIXELS; i++)
  {
    //TODO parameterize the color control
    ring.setPixelColor(i, ring.Color(250, 200, 200));
  }
  ring.show();
  delay(100);
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

          controllNeoPixel(is_on ? LISTENING_STATE : LOW);
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

  if (furhat_state == 0)
  {          
    controllNeoPixel( LISTENING_STATE);
  } 
  else
  {
    controllNeoPixel( furhat_state < BASE_STATE ? BASE_STATE : furhat_state);
  }
  
  delay(100);
}

void loop()
{
  toogleSystem(digitalRead(BTN_PIN)); 

  if(!is_on)
      return;
  else
    changeLedBaseOnSerialMessages();

}
