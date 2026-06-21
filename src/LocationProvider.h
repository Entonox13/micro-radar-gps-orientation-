#pragma once

#include <Arduino.h>

class LocationProvider
{
private:
    HardwareSerial& gpsSerial;
    bool enabled = false;
    bool hasFix = false;
    double latitude = 0.0;
    double longitude = 0.0;
    float hdop = 99.0f;
    unsigned long lastUpdateMs = 0;
    unsigned long lastFixMs = 0;

    static constexpr unsigned long FIX_TIMEOUT_MS = 10000;

    static float HaversineMetres(double lat1, double lon1, double lat2, double lon2);

public:
    explicit LocationProvider(HardwareSerial& serial) : gpsSerial(serial) {}

    void Initialise(bool gpsEnabled);
    void Update();

    [[nodiscard]] bool IsEnabled() const { return enabled; }
    [[nodiscard]] bool HasFix() const { return hasFix && (millis() - lastFixMs) < FIX_TIMEOUT_MS; }
    [[nodiscard]] double Latitude() const { return latitude; }
    [[nodiscard]] double Longitude() const { return longitude; }
    [[nodiscard]] float Hdop() const { return hdop; }
    [[nodiscard]] unsigned long LastUpdateMs() const { return lastUpdateMs; }

    bool TryUpdatePosition(double& outLat, double& outLon);
};
