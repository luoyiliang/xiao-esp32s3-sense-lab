#include <Wire.h>

static constexpr uint8_t SDA_PIN = 5;
static constexpr uint8_t SCL_PIN = 6;
static constexpr uint8_t ADDRS[] = {0x68, 0x69};

bool write16(uint8_t address, uint8_t reg, uint16_t value) {
  Wire.beginTransmission(address);
  Wire.write(reg);
  Wire.write(static_cast<uint8_t>(value & 0xff));
  Wire.write(static_cast<uint8_t>(value >> 8));
  return Wire.endTransmission() == 0;
}

bool read16(uint8_t address, uint8_t reg, uint16_t *value) {
  Wire.beginTransmission(address);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0) return false;
  uint8_t received = Wire.requestFrom(address, static_cast<uint8_t>(4), true);
  if (received != 4 || Wire.available() < 4) return false;
  Wire.read();
  Wire.read();
  uint8_t lo = Wire.read();
  uint8_t hi = Wire.read();
  *value = static_cast<uint16_t>(lo) | (static_cast<uint16_t>(hi) << 8);
  return true;
}

void probe(uint8_t address) {
  uint16_t id = 0;
  uint16_t status = 0;
  bool idBefore = read16(address, 0x00, &id);
  bool statusBefore = read16(address, 0x02, &status);
  Serial.printf("PROBE 0x%02X BEFORE id=%s 0x%04X status=%s 0x%04X\n",
                address, idBefore ? "OK" : "FAIL", id,
                statusBefore ? "OK" : "FAIL", status);

  bool resetWrite = write16(address, 0x7E, 0xDEAF);
  delay(10);
  id = 0;
  status = 0;
  bool idAfter = read16(address, 0x00, &id);
  bool statusAfter = read16(address, 0x02, &status);
  Serial.printf("PROBE 0x%02X RESET write=%s AFTER id=%s 0x%04X status=%s 0x%04X\n",
                address, resetWrite ? "OK" : "FAIL",
                idAfter ? "OK" : "FAIL", id,
                statusAfter ? "OK" : "FAIL", status);
}

void setup() {
  Serial.begin(115200);
  delay(1200);
  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(100000);
  Serial.println("READY BMI323_RAW_PROBE");
  for (uint8_t address : ADDRS) probe(address);
}

void loop() {
  delay(1000);
}
