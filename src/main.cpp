#include <Arduino.h>
#include <ArduinoJson.h>
#include <WiFiManager.h>

#include "LGFX.h"
#include "SensorConfig.h"
#include "WiFiManagerHelpers.h"
#include "ConfigurationWebServer.h"
#include "HttpRequestManager.h"
#include "OpenSkyAuthTokenHandler.h"
#include "LocationProvider.h"
#include "OrientationProvider.h"
#include "AircraftManager.h"
#include "DrawHelpers.h"
#include "models/Aircraft.h"
#include "models/TrackedAircraft.h"

constexpr int SCREEN_SIZE = 240;
constexpr int SCREEN_SIZE_DIV_2 = (SCREEN_SIZE / 2);

LGFX tft;
LGFX_Sprite backbuffer(&tft);

WiFiManager wm;
ConfigurationWebServer configServer;
HttpRequestManager http;
OpenSkyAuthTokenHandler authHandler(http);

HardwareSerial gpsSerial(1);
LocationProvider locationProvider(gpsSerial);
OrientationProvider orientationProvider;

AircraftManager aircraftManager(configServer, authHandler, http, tft, locationProvider, orientationProvider);

void ApplyPowerSettings()
{
    const bool batteryMode = configServer.GetStoredString("battery-mode") == "true";
    if (batteryMode) {
        WiFi.setSleep(WIFI_PS_MIN_MODEM);
        analogWrite(3, BATTERY_BACKLIGHT);
        Serial.println("[POWER] Battery mode enabled");
    } else {
        WiFi.setSleep(WIFI_PS_NONE);
        analogWrite(3, NORMAL_BACKLIGHT);
    }
}

void setup()
{
  Serial.begin(115200);

  tft.init();
  tft.invertDisplay(true);
  pinMode(3, OUTPUT);
  analogWrite(3, NORMAL_BACKLIGHT);

  backbuffer.setColorDepth(8);
  backbuffer.createSprite(SCREEN_SIZE, SCREEN_SIZE);

  tft.fillScreen(lgfx::color888(0, 0, 0));
  tft.setTextColor(lgfx::color888(0, 255, 0));
  tft.drawCentreString("Connecting to WiFi...", SCREEN_SIZE / 2, SCREEN_SIZE / 2);

  WiFiManagerHelpers::ConfigureWiFiManager(wm, tft);
  wm.autoConnect(WiFiManagerHelpers::WiFiManagerName);

  const bool gpsEnabled = configServer.GetStoredString("gps-mode") == "true";
  const bool compassEnabled = configServer.GetStoredString("compass-mode") == "true";
  const float compassOffset = configServer.GetStoredString("compass-offset").toFloat();

  locationProvider.Initialise(gpsEnabled);
  orientationProvider.Initialise(compassEnabled, compassOffset);

  configServer.SetSensorProviders(locationProvider, orientationProvider, aircraftManager);
  configServer.Initialise();

  ApplyPowerSettings();
  aircraftManager.Initialise();
}

void loop()
{
  locationProvider.Update();
  orientationProvider.Update();
  aircraftManager.Update();

  backbuffer.fillScreen(lgfx::color888(0, 0, 0));

  String renderScanlines = configServer.GetStoredString("scanline");
  if (renderScanlines.isEmpty() || renderScanlines == "true") {
    const int centreX = SCREEN_SIZE_DIV_2 - 1;
    const int centreY = SCREEN_SIZE_DIV_2 - 1;
    const int radius = SCREEN_SIZE_DIV_2 - 1;

    float sweepAngle;
    if (aircraftManager.IsCompassRotationEnabled() && orientationProvider.IsAvailable())
      sweepAngle = radians(aircraftManager.GetHeadingDeg());
    else
      sweepAngle = millis() / 3000.0f;

    const int endX = centreX + static_cast<int>(cos(sweepAngle) * radius);
    const int endY = centreY + static_cast<int>(sin(sweepAngle) * radius);

    DrawScanLines(backbuffer, centreX, centreY, endX, endY, 20, 128, 5);
  }

  aircraftManager.Draw(backbuffer);
  backbuffer.pushSprite(0, 0);
}
