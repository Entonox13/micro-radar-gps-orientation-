#pragma once

// GPS module (NEO-6M / ATGM336H / similar) on UART1
constexpr int GPS_RX_PIN = 4;
constexpr int GPS_TX_PIN = 5;
constexpr uint32_t GPS_BAUD = 9600;

// QMC5883L magnetometer on I2C
constexpr int I2C_SDA_PIN = 8;
constexpr int I2C_SCL_PIN = 9;
constexpr uint8_t QMC5883L_ADDRESS = 0x0D;

// Minimum GPS movement (metres) before updating the radar centre
constexpr float GPS_MIN_MOVE_METRES = 10.0f;

// Compass smoothing (0.0 = no smoothing, 0.95 = very smooth)
constexpr float COMPASS_SMOOTHING = 0.85f;

// Battery mode backlight level (0-255)
constexpr uint8_t BATTERY_BACKLIGHT = 64;
constexpr uint8_t NORMAL_BACKLIGHT = 255;
