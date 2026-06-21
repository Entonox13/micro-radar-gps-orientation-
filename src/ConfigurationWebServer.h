#pragma once

#include <ESPAsyncWebServer.h>
#include <Preferences.h>

class LocationProvider;
class OrientationProvider;
class AircraftManager;

class ConfigurationWebServer {
private:
    AsyncWebServer server;
    Preferences prefs;
    LocationProvider* locationProvider = nullptr;
    OrientationProvider* orientationProvider = nullptr;
    AircraftManager* aircraftManager = nullptr;

public:
    ConfigurationWebServer() : server(80), prefs() {}
    ConfigurationWebServer(int port) : server(port), prefs() {}

    void SetSensorProviders(LocationProvider& gps, OrientationProvider& compass, AircraftManager& aircraft);
    void Initialise();
    [[nodiscard]] const String GetStoredString(const char* key);
};
