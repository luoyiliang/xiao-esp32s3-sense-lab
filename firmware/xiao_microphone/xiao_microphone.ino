#include <I2S.h>

#define SAMPLE_RATE 16000U
#define SAMPLE_BITS 16
#define RECORD_SECONDS 5U

static uint8_t *recordBuffer = nullptr;
static size_t recordBytes = SAMPLE_RATE * (SAMPLE_BITS / 8) * RECORD_SECONDS;
static bool micReady = false;

static void sendRecording() {
  size_t captured = 0;
  Serial.printf("RECORDING %u\n", static_cast<unsigned>(recordBytes));
  Serial.flush();

  esp_i2s::i2s_read(
      esp_i2s::I2S_NUM_0,
      recordBuffer,
      recordBytes,
      &captured,
      portMAX_DELAY);

  if (captured == 0) {
    Serial.println("ERR RECORD");
    return;
  }

  // The raw PDM path is quiet; apply a conservative 4x signed gain.
  int16_t *samples = reinterpret_cast<int16_t *>(recordBuffer);
  size_t sampleCount = captured / sizeof(int16_t);
  for (size_t i = 0; i < sampleCount; ++i) {
    int32_t amplified = static_cast<int32_t>(samples[i]) * 4;
    if (amplified > 32767) amplified = 32767;
    if (amplified < -32768) amplified = -32768;
    samples[i] = static_cast<int16_t>(amplified);
  }

  Serial.printf("PCM %u %u %u\n",
                static_cast<unsigned>(captured),
                static_cast<unsigned>(SAMPLE_RATE),
                static_cast<unsigned>(SAMPLE_BITS));
  Serial.write(recordBuffer, captured);
  Serial.print("\nENDPCM\n");
  Serial.flush();
}

void setup() {
  Serial.begin(115200);
  delay(1500);

  if (!psramFound()) {
    Serial.println("ERR PSRAM");
    return;
  }

  recordBuffer = static_cast<uint8_t *>(ps_malloc(recordBytes));
  if (!recordBuffer) {
    Serial.println("ERR ALLOC");
    return;
  }

  I2S.setAllPins(-1, 42, 41, -1, -1);
  if (!I2S.begin(PDM_MONO_MODE, SAMPLE_RATE, SAMPLE_BITS)) {
    Serial.println("ERR MIC_INIT");
    return;
  }

  micReady = true;
  Serial.printf("READY XIAO_MIC seconds=%u rate=%u bits=%u\n",
                static_cast<unsigned>(RECORD_SECONDS),
                static_cast<unsigned>(SAMPLE_RATE),
                static_cast<unsigned>(SAMPLE_BITS));
  Serial.println("Send RECORD");
}

void loop() {
  if (!micReady || !Serial.available()) {
    delay(10);
    return;
  }

  String command = Serial.readStringUntil('\n');
  command.trim();
  command.toUpperCase();
  if (command == "RECORD") {
    sendRecording();
  } else if (command.length()) {
    Serial.printf("ERR COMMAND %s\n", command.c_str());
  }
}
