#pragma once

#include <map>

#include "models/TrackedAircraft.h"
#include "ConfigurationWebServer.h"
#include "OpenSkyAuthTokenHandler.h"
#include "LocationProvider.h"
#include "OrientationProvider.h"
#include "LGFX.h"

class AircraftManager
{
private:
    double lat = 0.0;
    double lon = 0.0;
    double rad = 0.2;
    float headingDeg = 0.0f;
    bool rotateWithCompass = false;
    bool gpsPositionInitialised = false;
    std::map<String, TrackedAircraft> trackedAircraft;

    bool displayInfoText = true;
    bool displayTriangles = true;

    unsigned long fetchInterval = 0;
    unsigned long lastFetch = 999999;

    ConfigurationWebServer& configServer;
    OpenSkyAuthTokenHandler& authHandler;
    HttpRequestManager& http;
    LGFX& tft;
    LocationProvider& locationProvider;
    OrientationProvider& orientationProvider;

    void DrawRadarCircles(LGFX_Sprite& backbuffer) const;
    std::pair<int, int> ProjectCoordinateToScreen(float predLat, float predLon) const;
    void DrawAircraftInfo(LGFX_Sprite& backbuffer, int x, int y, const TrackedAircraft& tracked) const;
    void DrawAircraftTriangle(LGFX_Sprite& backbuffer, int x, int y, const TrackedAircraft& tracked) const;
    void UpdateLocationFromGps();
    void UpdateHeadingFromCompass();

public:
    AircraftManager(
        ConfigurationWebServer& config,
        OpenSkyAuthTokenHandler& auth,
        HttpRequestManager& httpManager,
        LGFX& tftGfx,
        LocationProvider& gps,
        OrientationProvider& compass
    )
        : configServer(config),
          authHandler(auth),
          http(httpManager),
          tft(tftGfx),
          locationProvider(gps),
          orientationProvider(compass)
    {
    }
    ~AircraftManager() = default;

    void Initialise();
    void Update();
    void Draw(LGFX_Sprite& backbuffer);

    [[nodiscard]] float GetHeadingDeg() const { return headingDeg; }
    [[nodiscard]] bool IsCompassRotationEnabled() const { return rotateWithCompass; }
    [[nodiscard]] double GetLatitude() const { return lat; }
    [[nodiscard]] double GetLongitude() const { return lon; }
};
