"""Radar canvas widget — mirrors the desktop Tkinter drawing."""

from __future__ import annotations

import math
import time

from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line, Rectangle, Triangle
from kivy.properties import BooleanProperty, NumericProperty, ObjectProperty
from kivy.uix.widget import Widget

from microradar_core.aircraft_labels import aircraft_info_label
from microradar_core.radar_engine import RadarEngine, SCREEN_SIZE


class RadarWidget(Widget):
    engine = ObjectProperty(None)
    scale = NumericProperty(1.0)
    show_border = BooleanProperty(True)
    double_tap_enabled = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._scan_phase = 0.0
        self._last_tap_time = 0.0
        self._double_tap_callback = None
        self.bind(size=self._redraw, pos=self._redraw)
        Clock.schedule_interval(self._tick, 1 / 20)

    def on_engine(self, _instance, engine: RadarEngine | None) -> None:
        if engine is not None:
            self._redraw()

    def set_double_tap_callback(self, callback) -> None:
        self._double_tap_callback = callback

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)

        if self.double_tap_enabled:
            now = time.monotonic()
            if now - self._last_tap_time < 0.35:
                if self._double_tap_callback:
                    self._double_tap_callback()
                return True
            self._last_tap_time = now
            return True

        return super().on_touch_down(touch)

    def _tick(self, _dt: float) -> None:
        if self.engine is None:
            return
        self._redraw()

    def _redraw(self, *_args) -> None:
        if self.canvas is None or self.engine is None or self.width <= 0 or self.height <= 0:
            return

        self.canvas.clear()

        side = min(self.width, self.height)
        scale = side / SCREEN_SIZE
        offset_x = self.x + (self.width - side) / 2
        offset_y = self.y + (self.height - side) / 2
        cx = offset_x + side / 2
        cy = offset_y + side / 2
        outer = side / 2 - 2 * scale

        with self.canvas:
            Color(0, 0, 0, 1)
            Rectangle(pos=(offset_x, offset_y), size=(side, side))

            if self.show_border:
                Color(0.133, 0.773, 0.369, 1)
                Line(
                    rectangle=(offset_x, offset_y, side, side),
                    width=2 * scale,
                )

            for factor, rgb in [
                (1.0, (0, 200 / 255, 0)),
                (2 / 3, (0, 64 / 255, 0)),
                (1 / 3, (0, 32 / 255, 0)),
            ]:
                r = outer * factor
                Color(*rgb, 1)
                Line(circle=(cx, cy, r), width=2 * scale)

            if self.engine.show_scanline:
                if self.engine.compass_mode:
                    angle = math.radians(self.engine.heading_deg)
                else:
                    self._scan_phase += 0.02
                    angle = self._scan_phase
                ex = cx + math.cos(angle) * outer
                ey = cy - math.sin(angle) * outer
                Color(0, 200 / 255, 0, 1)
                Line(points=[cx, cy, ex, ey], width=2 * scale)

            now_ms = self.engine.now_ms()
            for tracked, x, y in self.engine.visible_aircraft(now_ms):
                sx = offset_x + x * scale
                sy = offset_y + (SCREEN_SIZE - y) * scale

                if self.engine.show_triangles:
                    points = self.engine.triangle_points(tracked, x, y)
                    flat = []
                    for px, py in points:
                        flat.extend([offset_x + px * scale, offset_y + (SCREEN_SIZE - py) * scale])
                    Color(0, 1, 0, 1)
                    Triangle(points=flat)
                else:
                    r = 4 * scale
                    Color(0, 1, 0, 1)
                    Ellipse(pos=(sx - r, sy - r), size=(2 * r, 2 * r))

                if self.engine.show_info and tracked.state.callsign:
                    from kivy.core.text import Label as CoreLabel

                    label = CoreLabel(
                        text=aircraft_info_label(tracked.state),
                        font_size=9 * scale,
                        color=(0, 128 / 255, 0, 1),
                    )
                    label.refresh()
                    tex = label.texture
                    Color(1, 1, 1, 1)
                    Rectangle(
                        texture=tex,
                        pos=(sx + 8 * scale, sy + 8 * scale),
                        size=tex.size,
                    )

            dot = 3 * scale
            Color(0, 1, 0, 1)
            Ellipse(pos=(cx - dot, cy - dot), size=(2 * dot, 2 * dot))
