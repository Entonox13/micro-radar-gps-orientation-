#include "LocationProvider.h"
#include "SensorConfig.h"

#include <TinyGPSPlus.h>

namespace
{
    TinyGPSPlus gps;
}

void LocationProvider::Initialise(bool gpsEnabled)
{
    enabled = gpsEnabled;
    if (!enabled)
        return;

    gpsSerial.begin(GPS_BAUD, SERIAL_8N1, GPS_RX_PIN, GPS_TX_PIN);
    Serial.println("[GPS] UART initialised");
}

void LocationProvider::Update()
{
    if (!enabled)
        return;

    while (gpsSerial.available() > 0) {
        if (gps.encode(gpsSerial.read()))
            lastUpdateMs = millis();
    }

    if (gps.location.isValid()) {
        latitude = gps.location.lat();
        longitude = gps.location.lng();
        hasFix = true;
        lastFixMs = millis();
    }

    if (gps.hdop.isValid())
        hdop = static_cast<float>(gps.hdop.hdop());
}

float LocationProvider::HaversineMetres(double lat1, double lon1, double lat2, double lon2)
{
    constexpr double EARTH_RADIUS_M = 6371000.0;
    const double dLat = radians(lat2 - lat1);
    const double dLon = radians(lon2 - lon1);
    const double a = sin(dLat / 2.0) * sin(dLat / 2.0)
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon / 2.0) * sin(dLon / 2.0);
    return static_cast<float>(EARTH_RADIUS_M * 2.0 * atan2(sqrt(a), sqrt(1.0 - a)));
}

bool LocationProvider::TryUpdatePosition(double& outLat, double& outLon)
{
    if (!enabled || !HasFix())
        return false;

    const float distance = HaversineMetres(outLat, outLon, latitude, longitude);
    if (distance < GPS_MIN_MOVE_METRES)
        return false;

    outLat = latitude;
    outLon = longitude;
    return true;
}
