// MAX30102 on ESP32 (your pins): SDA=D4, SCL=D15
// Libraries: SparkFun MAX3010x Sensor Library (includes MAX30105.h, heartRate.h, spo2_algorithm.h)

#include <Wire.h>
#include "MAX30105.h"
#include "heartRate.h"
#include "spo2_algorithm.h"

MAX30105 sensor;

// Buffers for SpO2 algorithm
const int32_t N = 100;          // samples per calculation (~0.5s at 200 Hz)
uint32_t irBuf[N], redBuf[N];

int32_t spo2, heartRate;
int8_t validSPO2, validHR;

void setup() {
  Serial.begin(115200);
  delay(300);

  // Your working I2C pins
  Wire.begin(4, 15);            // SDA=D4, SCL=D15

  Serial.println("Initializing MAX30102...");
  if (!sensor.begin(Wire, I2C_SPEED_STANDARD)) {
    Serial.println("MAX30102 not found. Check wiring (VIN=3V3, GND, SDA=D4, SCL=D15).");
    while (1) { delay(1000); }
  }

  // Sensor configuration (good stable defaults)
  byte ledBrightness = 0x1F;    // LED current (0x02..0xFF). Increase if signal low.
  byte sampleAvg     = 4;       // 1,2,4,8,16,32
  byte ledMode       = 2;       // 1=Red only, 2=Red+IR (needed for SpO2)
  int  sampleRate    = 200;     // 50..3200 (Hz). 200 is a good start.
  int  pulseWidth    = 411;     // 69,118,215,411 (higher = more SNR)
  int  adcRange      = 16384;   // 2048,4096,8192,16384

  sensor.setup(ledBrightness, sampleAvg, ledMode, sampleRate, pulseWidth, adcRange);
  sensor.setPulseAmplitudeGreen(0);     // not used; turn off to save power

  Serial.println("Place finger gently over the sensor window...");
}

void loop() {
  // Fill buffers
  for (int i = 0; i < N; i++) {
    // Wait for a new sample
    while (!sensor.available()) sensor.check();

    redBuf[i] = sensor.getRed();
    irBuf[i]  = sensor.getIR();

    sensor.nextSample();
  }

  // Run Maxim algorithm (from SparkFun lib) to compute BPM & SpO2
  maxim_heart_rate_and_oxygen_saturation(
    irBuf, N,
    redBuf,
    &spo2, &validSPO2,
    &heartRate, &validHR
  );

  // Print results
  Serial.print("BPM=");    Serial.print(validHR   ? heartRate : -1);
  Serial.print("  SpO2=%");Serial.print(validSPO2 ? spo2      : -1);
  Serial.print("  IR=");   Serial.print(irBuf[N-1]);
  Serial.print("  RED=");  Serial.println(redBuf[N-1]);

  delay(200); // small delay between batches
}
