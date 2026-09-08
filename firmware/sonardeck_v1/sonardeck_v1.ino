/*
  SonarDeck V1 firmware for Console Deck V2 hardware

  Goals:
  - No OLED/display required.
  - Arduino only reports hardware events over USB serial.
  - PC bridge decides what each event does.
  - Button 10 supports short press vs long press for play/pause + page/profile switching.

  Wiring:
  - Buttons are wired from Arduino pin to GND.
  - Firmware uses INPUT_PULLUP, so pressed == LOW.
  - Rotary encoder uses CLK, DT, SW.

  Serial events:
  - BTN_01_PRESS ... BTN_10_PRESS
  - BTN_10_LONG
  - ENC_01_CW
  - ENC_01_CCW
  - ENC_01_PRESS
*/

#define ENCODER_CLK 5
#define ENCODER_DT 4
#define ENCODER_SW 3

// Keep this order stable: physical/logical button number -> pin.
// Based on the original Console Deck V2 sketch and the provided schematic.
const byte BUTTON_COUNT = 10;
const byte buttonPins[BUTTON_COUNT] = {
  2,   // BTN_01 - schematic SW11
  A1,  // BTN_02 - schematic SW8
  A0,  // BTN_03 - schematic SW9
  11,  // BTN_04 - schematic SW5
  10,  // BTN_05 - schematic SW6
  9,   // BTN_06 - schematic SW7
  12,  // BTN_07 - schematic SW10 (uses D12; original sketch used D2 here)
  6,   // BTN_08 - schematic SW2
  7,   // BTN_09 - schematic SW3
  A2   // BTN_10 - dedicated play/pause; long press switches profile/page (adjust pin if your final wiring differs)
};

const unsigned long DEBOUNCE_MS = 35;
const unsigned long LONG_PRESS_MS = 650;

bool lastReading[BUTTON_COUNT];
bool stableState[BUTTON_COUNT];
unsigned long lastChangeMs[BUTTON_COUNT];
unsigned long pressedAtMs[BUTTON_COUNT];
bool longSent[BUTTON_COUNT];

int lastEncoderClk;
bool lastEncoderButtonReading = HIGH;
bool encoderButtonStable = HIGH;
unsigned long encoderButtonChangedMs = 0;

void printButtonEvent(byte logicalIndex, const char* suffix) {
  Serial.print("BTN_");
  if (logicalIndex < 10) Serial.print("0");
  Serial.print(logicalIndex);
  Serial.print("_");
  Serial.println(suffix);
}

void setupButtons() {
  for (byte i = 0; i < BUTTON_COUNT; i++) {
    pinMode(buttonPins[i], INPUT_PULLUP);
    bool reading = digitalRead(buttonPins[i]);
    lastReading[i] = reading;
    stableState[i] = reading;
    lastChangeMs[i] = 0;
    pressedAtMs[i] = 0;
    longSent[i] = false;
  }
}

void setupEncoder() {
  pinMode(ENCODER_CLK, INPUT);
  pinMode(ENCODER_DT, INPUT);
  pinMode(ENCODER_SW, INPUT_PULLUP);
  lastEncoderClk = digitalRead(ENCODER_CLK);
}

void setup() {
  Serial.begin(9600);
  setupButtons();
  setupEncoder();
  Serial.println("SONARDECK_READY");
}

void loopButtons() {
  unsigned long now = millis();

  for (byte i = 0; i < BUTTON_COUNT; i++) {
    bool reading = digitalRead(buttonPins[i]);

    if (reading != lastReading[i]) {
      lastReading[i] = reading;
      lastChangeMs[i] = now;
    }

    if ((now - lastChangeMs[i]) >= DEBOUNCE_MS && reading != stableState[i]) {
      stableState[i] = reading;

      if (stableState[i] == LOW) {
        pressedAtMs[i] = now;
        longSent[i] = false;
      } else {
        byte logicalButton = i + 1;
        unsigned long heldMs = now - pressedAtMs[i];

        // Button 10 is the play/pause button: short press maps to play/pause,
        // long press sends BTN_10_LONG and suppresses BTN_10_PRESS.
        if (logicalButton == 10 && heldMs >= LONG_PRESS_MS) {
          if (!longSent[i]) printButtonEvent(logicalButton, "LONG");
        } else if (!longSent[i]) {
          printButtonEvent(logicalButton, "PRESS");
        }
      }
    }

    // Send long-press once while still held so the bridge can switch immediately.
    if (stableState[i] == LOW && (i + 1) == 10 && !longSent[i] && (now - pressedAtMs[i]) >= LONG_PRESS_MS) {
      printButtonEvent(10, "LONG");
      longSent[i] = true;
    }
  }
}

void loopEncoderRotation() {
  int currentClk = digitalRead(ENCODER_CLK);
  if (currentClk != lastEncoderClk) {
    if (digitalRead(ENCODER_DT) != currentClk) {
      Serial.println("ENC_01_CW");
    } else {
      Serial.println("ENC_01_CCW");
    }
  }
  lastEncoderClk = currentClk;
}

void loopEncoderButton() {
  unsigned long now = millis();
  bool reading = digitalRead(ENCODER_SW);

  if (reading != lastEncoderButtonReading) {
    lastEncoderButtonReading = reading;
    encoderButtonChangedMs = now;
  }

  if ((now - encoderButtonChangedMs) >= DEBOUNCE_MS && reading != encoderButtonStable) {
    encoderButtonStable = reading;
    if (encoderButtonStable == LOW) {
      Serial.println("ENC_01_PRESS");
    }
  }
}

void loop() {
  loopButtons();
  loopEncoderRotation();
  loopEncoderButton();
}
