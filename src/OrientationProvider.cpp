#include "OrientationProvider.h"
#include "SensorConfig.h"

#include <Wire.h>

namespace
{
    constexpr uint8_t QMC_REG_X_LSB = 0x00;
    constexpr uint8_t QMC_REG_STATUS = 0x06;
    constexpr uint8_t QMC_REG_CONTROL_1 = 0x09;
    constexpr uint8_t QMC_REG_SET_RESET = 0x0B;

    constexpr uint8_t QMC_STATUS_DATA_READY = 0x01;
    constexpr uint8_t QMC_MODE_CONTINUOUS = 0x1D;
}

void OrientationProvider::Initialise(bool compassEnabled, float storedOffset)
{
    enabled = compassEnabled;
    calibrationOffset = storedOffset;

    if (!enabled)
        return;

    Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
    Wire.setClock(100000);

    available = DetectSensor();
    if (available)
        Serial.println("[COMPASS] QMC5883L detected");
    else
        Serial.println("[WARN] Compass enabled but no QMC5883L found on I2C bus");
}

bool OrientationProvider::DetectSensor()
{
    Wire.beginTransmission(QMC5883L_ADDRESS);
    if (Wire.endTransmission() != 0)
        return false;

    Wire.write(QMC_REG_SET_RESET);
    Wire.write(0x01);
    Wire.endTransmission();

    Wire.beginTransmission(QMC5883L_ADDRESS);
    Wire.write(QMC_REG_CONTROL_1);
    Wire.write(QMC_MODE_CONTINUOUS);
  return Wire.endTransmission() == 0;
}

bool OrientationProvider::ReadRaw(int16_t& x, int16_t& y, int16_t& z)
{
    Wire.beginTransmission(QMC5883L_ADDRESS);
    Wire.write(QMC_REG_X_LSB);
    if (Wire.endTransmission(false) != 0)
        return false;

    if (Wire.requestFrom(QMC5883L_ADDRESS, static_cast<uint8_t>(6)) != 6)
        return false;

    const uint8_t xLsb = Wire.read();
    const uint8_t xMsb = Wire.read();
    const uint8_t yLsb = Wire.read();
    const uint8_t yMsb = Wire.read();
    const uint8_t zLsb = Wire.read();
    const uint8_t zMsb = Wire.read();

    x = static_cast<int16_t>((xMsb << 8) | xLsb);
    y = static_cast<int16_t>((yMsb << 8) | yLsb);
    z = static_cast<int16_t>((zMsb << 8) | zLsb);
    return true;
}

float OrientationProvider::NormaliseHeading(float heading)
{
    while (heading < 0.0f)
        heading += 360.0f;
    while (heading >= 360.0f)
        heading -= 360.0f;
    return heading;
}

void OrientationProvider::Update()
{
    if (!enabled || !available)
        return;

    const unsigned long now = millis();
    if (now - lastReadMs < READ_INTERVAL_MS)
        return;
    lastReadMs = now;

    int16_t x = 0;
    int16_t y = 0;
    int16_t z = 0;
    if (!ReadRaw(x, y, z))
        return;

    const float rawHeading = degrees(atan2f(static_cast<float>(y), static_cast<float>(x)));
    const float corrected = NormaliseHeading(rawHeading + calibrationOffset);

    if (!hasHeading) {
        headingDeg = corrected;
        hasHeading = true;
    } else {
        headingDeg = NormaliseHeading(headingDeg * COMPASS_SMOOTHING + corrected * (1.0f - COMPASS_SMOOTHING));
    }
}

void OrientationProvider::SetCalibrationOffset(float offset)
{
    calibrationOffset = offset;
}
