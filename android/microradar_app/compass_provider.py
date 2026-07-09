"""Smartphone compass via Android SensorManager (pyjnius)."""

from __future__ import annotations

import math
from typing import Callable

from microradar_app.config import platform_name

COMPASS_SMOOTHING = 0.85
READ_INTERVAL_S = 0.05


def _normalise_heading(heading: float) -> float:
    return heading % 360.0


class CompassProvider:
    def __init__(self) -> None:
        self.enabled = False
        self.available = False
        self.has_heading = False
        self.heading_deg = 0.0
        self.calibration_offset = 0.0
        self._on_update: Callable[[float], None] | None = None
        self._last_read_monotonic = 0.0
        self._backend: _CompassBackend | None = None

    def set_calibration_offset(self, offset: float) -> None:
        self.calibration_offset = offset

    def set_update_callback(self, callback: Callable[[float], None] | None) -> None:
        self._on_update = callback

    def start(self) -> None:
        if self._backend is None:
            self._backend = create_compass_backend(self)
        self._backend.start()
        self.available = self._backend.is_available()

    def stop(self) -> None:
        if self._backend is not None:
            self._backend.stop()

    def set_active(self, active: bool) -> None:
        self.enabled = active
        if self._backend is not None:
            self._backend.set_listening(active)

    def _apply_heading(self, raw_heading: float) -> None:
        import time

        now = time.monotonic()
        if now - self._last_read_monotonic < READ_INTERVAL_S:
            return
        self._last_read_monotonic = now

        corrected = _normalise_heading(raw_heading + self.calibration_offset)
        if not self.has_heading:
            self.heading_deg = corrected
            self.has_heading = True
        else:
            delta = ((corrected - self.heading_deg + 180.0) % 360.0) - 180.0
            self.heading_deg = _normalise_heading(
                self.heading_deg + delta * (1.0 - COMPASS_SMOOTHING)
            )

        if self._on_update:
            self._on_update(self.heading_deg)


class _CompassBackend:
    def start(self) -> None:
        raise NotImplementedError

    def stop(self) -> None:
        raise NotImplementedError

    def set_listening(self, active: bool) -> None:
        raise NotImplementedError

    def is_available(self) -> bool:
        raise NotImplementedError


class _NullCompassBackend(_CompassBackend):
    def __init__(self, provider: CompassProvider) -> None:
        self._provider = provider

    def start(self) -> None:
        self._provider.available = False

    def stop(self) -> None:
        pass

    def set_listening(self, active: bool) -> None:
        pass

    def is_available(self) -> bool:
        return False


class _AndroidCompassBackend(_CompassBackend):
    def __init__(self, provider: CompassProvider) -> None:
        self._provider = provider
        self._sensor_manager = None
        self._listener = None
        self._rotation_sensor = None
        self._accel_sensor = None
        self._magnet_sensor = None
        self._accel: list[float] | None = None
        self._magnet: list[float] | None = None
        self._listening = False
        self._use_rotation_vector = False
        self._Sensor = None
        self._SensorManager = None

    def is_available(self) -> bool:
        return self._rotation_sensor is not None or (
            self._accel_sensor is not None and self._magnet_sensor is not None
        )

    def start(self) -> None:
        try:
            from jnius import PythonJavaClass, autoclass, java_method

            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Context = autoclass("android.content.Context")
            self._SensorManager = autoclass("android.hardware.SensorManager")
            self._Sensor = autoclass("android.hardware.Sensor")

            activity = PythonActivity.mActivity
            if activity is None:
                return
            self._sensor_manager = activity.getSystemService(Context.SENSOR_SERVICE)
            if self._sensor_manager is None:
                return

            self._rotation_sensor = self._sensor_manager.getDefaultSensor(
                self._Sensor.TYPE_ROTATION_VECTOR
            )
            if self._rotation_sensor is None:
                self._rotation_sensor = self._sensor_manager.getDefaultSensor(
                    self._Sensor.TYPE_GAME_ROTATION_VECTOR
                )

            if self._rotation_sensor is not None:
                self._use_rotation_vector = True
            else:
                self._accel_sensor = self._sensor_manager.getDefaultSensor(
                    self._Sensor.TYPE_ACCELEROMETER
                )
                self._magnet_sensor = self._sensor_manager.getDefaultSensor(
                    self._Sensor.TYPE_MAGNETIC_FIELD
                )

            backend = self

            class SensorListener(PythonJavaClass):
                __javainterfaces__ = ["android/hardware/SensorEventListener"]
                __javacontext__ = "app"

                @java_method("(Landroid/hardware/SensorEvent;)V")
                def onSensorChanged(self, event):
                    backend._on_sensor_event(event)

                @java_method("(Landroid/hardware/Sensor;I)V")
                def onAccuracyChanged(self, sensor, accuracy):
                    pass

            self._listener = SensorListener()
            self._provider.available = self.is_available()
            if self._listening:
                self._register_sensors()
        except Exception:
            self._provider.available = False

    def stop(self) -> None:
        self._unregister_sensors()

    def set_listening(self, active: bool) -> None:
        self._listening = active
        if self._sensor_manager is None:
            return
        if active:
            self._register_sensors()
        else:
            self._unregister_sensors()

    def _register_sensors(self) -> None:
        if self._sensor_manager is None or self._listener is None or self._SensorManager is None:
            return
        delay = self._SensorManager.SENSOR_DELAY_UI
        if self._use_rotation_vector and self._rotation_sensor is not None:
            self._sensor_manager.registerListener(
                self._listener, self._rotation_sensor, delay
            )
        elif self._accel_sensor is not None and self._magnet_sensor is not None:
            self._sensor_manager.registerListener(self._listener, self._accel_sensor, delay)
            self._sensor_manager.registerListener(self._listener, self._magnet_sensor, delay)

    def _unregister_sensors(self) -> None:
        if self._sensor_manager is not None and self._listener is not None:
            self._sensor_manager.unregisterListener(self._listener)

    def _on_sensor_event(self, event) -> None:
        try:
            if self._Sensor is None or self._SensorManager is None:
                return

            values = [event.values[i] for i in range(event.values.length)]

            if self._use_rotation_vector:
                heading = self._heading_from_rotation_vector(values)
            else:
                sensor_type = event.sensor.getType()
                if sensor_type == self._Sensor.TYPE_ACCELEROMETER:
                    self._accel = values
                elif sensor_type == self._Sensor.TYPE_MAGNETIC_FIELD:
                    self._magnet = values
                else:
                    return
                if self._accel is None or self._magnet is None:
                    return
                heading = self._heading_from_accel_magnet(self._accel, self._magnet)

            if heading is None:
                return

            def deliver(_dt: float) -> None:
                if self._listening:
                    self._provider._apply_heading(heading)

            from kivy.clock import Clock

            Clock.schedule_once(deliver, 0)
        except Exception:
            pass

    def _heading_from_rotation_vector(self, values: list[float]) -> float | None:
        rotation_matrix = [0.0] * 9
        self._SensorManager.getRotationMatrixFromVector(rotation_matrix, values)
        return self._orientation_heading(rotation_matrix)

    def _heading_from_accel_magnet(
        self, accel: list[float], magnet: list[float]
    ) -> float | None:
        rotation_matrix = [0.0] * 9
        inclination = [0.0] * 9
        if not self._SensorManager.getRotationMatrix(
            rotation_matrix, inclination, accel, magnet
        ):
            return None
        return self._orientation_heading(rotation_matrix)

    def _orientation_heading(self, rotation_matrix: list[float]) -> float | None:
        remapped = [0.0] * 9
        self._SensorManager.remapCoordinateSystem(
            rotation_matrix,
            self._SensorManager.AXIS_Y,
            self._SensorManager.AXIS_MINUS_X,
            remapped,
        )
        orientation = [0.0] * 3
        self._SensorManager.getOrientation(remapped, orientation)
        azimuth = math.degrees(orientation[0])
        return _normalise_heading(azimuth)


def create_compass_backend(provider: CompassProvider) -> _CompassBackend:
    if platform_name() == "android":
        try:
            return _AndroidCompassBackend(provider)
        except Exception:
            return _NullCompassBackend(provider)
    return _NullCompassBackend(provider)
