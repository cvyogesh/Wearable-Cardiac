// === ESP32 + AD8232 ECG (slow output + basic BPM) ============================
// Wiring:
//   AD8232 3.3V  -> ESP32 3V3
//   AD8232 GND   -> ESP32 GND
//   AD8232 OUT   -> ESP32 GPIO34 (D34)   <-- use 32/33/34/35/36/39 (ADC1 pins)
//   LO+/LO- not required for basic plot
//
// How to view:
//   Tools -> Serial Plotter, 115200 baud  (you'll see a single ECG trace)
//   BPM is also printed once per second in plain text (ignore in Plotter)
//
// If you used a different pin, set ECG_PIN below accordingly.
//
// Notes:
// - Keep still, good electrode contact: RED=right upper chest, YELLOW=left upper chest, GREEN=lower right abdomen.
// - Power from laptop USB or battery only (no mains-connected gear on your body).

// ---------------------- USER SETTINGS ----------------------
const int ECG_PIN = 34;      // <-- change to 32 or 33 if you wired there
const int SAMPLE_DELAY_MS = 5;     // ~200 Hz sampling (ECG-friendly)
const int PRINT_EVERY = 5;         // print every Nth sample (reduces scroll ~40 Hz)
// Filtering (tune if needed)
float hpAlpha = 0.995f;      // high-pass factor for baseline removal (0.99..0.999)
float lpAlpha = 0.20f;       // low-pass EMA smoothing (0..1; higher = smoother)
// Peak detect / BPM
const int REFRACT_MS = 250;  // minimum time between peaks (beats) in ms (avoid double counts)
const float THRESH_INIT = 80; // starting threshold in filtered units (auto-updates)

// ---------------------- INTERNAL STATE --------------------
float baseline = 0.0f;     // for high-pass
float smooth   = 0.0f;     // for low-pass
float dynThresh = THRESH_INIT;
float envEMA = 0.0f;       // track envelope for adaptive threshold

unsigned long lastPeakMs = 0;
unsigned long lastPrintBPMms = 0;
float bpmEMA = 0.0f;       // smoothed BPM display

// helper for adaptive thresholding
float absf(float x) { return (x < 0) ? -x : x; }

void setup() {
  Serial.begin(115200);
  delay(300);
  Serial.println("ECG started. Open Serial Plotter @ 115200. Sit still for best results.");

  // (Optional) you can set ADC attenuation if you like; defaults work fine
  // analogSetPinAttenuation(ECG_PIN, ADC_11db); // gives wider input range
}

void loop() {
  // 1) Sample raw ECG
  int raw = analogRead(ECG_PIN);        // 0..4095
  // 2) High-pass (remove baseline drift)
  baseline = hpAlpha * baseline + (1.0f - hpAlpha) * raw;
  float hp = raw - baseline;            // centered near 0
  // 3) Low-pass (EMA smoothing)
  smooth = lpAlpha * hp + (1.0f - lpAlpha) * smooth;

  // 4) Adaptive envelope + threshold
  envEMA = 0.01f * absf(smooth) + 0.99f * envEMA;  // slow envelope
  // Threshold follows a fraction of the envelope; tweak 0.35 if needed
  dynThresh = 0.35f * envEMA + 30.0f;              // small bias to avoid zero

  // 5) Simple peak detection (rising edge above threshold with refractory)
  static bool above = false;
  unsigned long nowMs = millis();
  if (!above && smooth > dynThresh) {
    above = true;
    // check refractory
    if (nowMs - lastPeakMs > (unsigned long)REFRACT_MS) {
      if (lastPeakMs != 0) {
        float ibi_ms = (float)(nowMs - lastPeakMs);  // inter-beat interval
        float instBPM = 60000.0f / ibi_ms;
        // smooth BPM display
        if (bpmEMA <= 0.01f) bpmEMA = instBPM;
        bpmEMA = 0.2f * instBPM + 0.8f * bpmEMA;
      }
      lastPeakMs = nowMs;
    }
  } else if (above && smooth < 0) {
    // reset latch once we crossed back down
    above = false;
  }

  // 6) Slow down printed stream for readability/Plotter
  static uint32_t sampleCount = 0;
  sampleCount++;
  if (sampleCount % PRINT_EVERY == 0) {
    // Shift to positive for Plotter (expects numeric lines)
    int plotVal = (int)(smooth + 2048.0f);
    Serial.println(plotVal);
  }

  // 7) Also print BPM about once a second (text line; Plotter will ignore it)
  if (nowMs - lastPrintBPMms > 1000) {
    lastPrintBPMms = nowMs;
    if (bpmEMA > 20 && bpmEMA < 200) {
      Serial.print("BPM: ");
      Serial.println((int)(bpmEMA + 0.5f));
    } else {
      Serial.println("BPM: --");
    }
  }

  delay(SAMPLE_DELAY_MS);  // controls sample rate (~200 Hz at 5ms)
}
