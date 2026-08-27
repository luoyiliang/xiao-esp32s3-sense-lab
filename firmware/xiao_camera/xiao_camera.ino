#include "esp_camera.h"

// Seeed Studio XIAO ESP32S3 Sense camera pins
#define PWDN_GPIO_NUM  -1
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM  10
#define SIOD_GPIO_NUM  40
#define SIOC_GPIO_NUM  39
#define Y9_GPIO_NUM    48
#define Y8_GPIO_NUM    11
#define Y7_GPIO_NUM    12
#define Y6_GPIO_NUM    14
#define Y5_GPIO_NUM    16
#define Y4_GPIO_NUM    18
#define Y3_GPIO_NUM    17
#define Y2_GPIO_NUM    15
#define VSYNC_GPIO_NUM 38
#define HREF_GPIO_NUM  47
#define PCLK_GPIO_NUM  13

static bool cameraReady = false;

static void sendFrame() {
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("ERR CAPTURE");
    return;
  }

  Serial.printf("JPEG %u\n", static_cast<unsigned>(fb->len));
  Serial.write(fb->buf, fb->len);
  Serial.print("\nENDJPEG\n");
  Serial.flush();
  esp_camera_fb_return(fb);
}

void setup() {
  Serial.begin(115200);
  delay(1500);

  camera_config_t config = {};
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_VGA;
  config.jpeg_quality = 12;
  config.fb_count = psramFound() ? 2 : 1;
  config.grab_mode = CAMERA_GRAB_LATEST;
  config.fb_location = psramFound() ? CAMERA_FB_IN_PSRAM : CAMERA_FB_IN_DRAM;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("ERR CAMERA_INIT 0x%x\n", err);
    return;
  }

  cameraReady = true;
  Serial.printf("READY XIAO_CAMERA PSRAM=%s\n", psramFound() ? "YES" : "NO");
  Serial.println("Send CAPTURE");
}

void loop() {
  if (!cameraReady || !Serial.available()) {
    delay(10);
    return;
  }

  String command = Serial.readStringUntil('\n');
  command.trim();
  command.toUpperCase();
  if (command == "CAPTURE") {
    sendFrame();
  } else if (command.length()) {
    Serial.printf("ERR COMMAND %s\n", command.c_str());
  }
}
