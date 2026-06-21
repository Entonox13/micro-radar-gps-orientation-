#pragma once

#include <Arduino.h>

class OrientationProvider
{
private:
    bool enabled = false;
    bool available = false;
    float headingDeg = 0.0f;
    float calibrationOffset = 0.0f;
    bool hasHeading = false;
    unsigned long lastReadMs = 0;

    static constexpr unsigned long READ_INTERVAL_MS = 50;

    bool DetectSensor();
    bool ReadRaw(int16_t& x, int16_t& y, int16_t& z);
    static float NormaliseHeading(float heading);

public:
    void Initialise(bool compassEnabled, float storedOffset);
    void Update();

    [[nodiscard]] bool IsEnabled() const { return enabled; }
    [[nodiscard]] bool IsAvailable() const { return available; }
    [[nodiscard]] float HeadingDeg() const { return headingDeg; }
    [[nodiscard]] float CalibrationOffset() const { return calibrationOffset; }

    void SetCalibrationOffset(float offset);
};
