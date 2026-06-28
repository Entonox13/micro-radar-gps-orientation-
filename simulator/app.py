#!/usr/bin/env python3
"""Desktop simulator for Micro Radar — test OpenSky coverage at your location."""

from __future__ import annotations

import json
import math
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from opensky_client import OpenSkyClient, geolocate_ip
from radar_engine import SCREEN_SIZE, RadarEngine

CONFIG_PATH = Path(__file__).with_name("config.json")
CANVAS_SCALE = 2
CANVAS_SIZE = SCREEN_SIZE * CANVAS_SCALE


class MicroRadarApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Micro Radar — Simulateur")
        self.minsize(900, 620)
        self.configure(bg="#111827")

        self.engine = RadarEngine(client=OpenSkyClient())
        self._scan_phase = 0.0
        self._busy = False

        self._build_ui()
        self._load_config()
        self._apply_settings_to_engine()
        self._draw_frame()
        self.after(50, self._tick)

    def _build_ui(self) -> None:
        main = ttk.Frame(self, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(main)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)

        self.canvas = tk.Canvas(
            left,
            width=CANVAS_SIZE,
            height=CANVAS_SIZE,
            bg="black",
            highlightthickness=2,
            highlightbackground="#22c55e",
        )
        self.canvas.pack()

        right = ttk.Frame(main, padding=(16, 0, 0, 0))
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        title = ttk.Label(right, text="Configuration", font=("TkDefaultFont", 14, "bold"))
        title.pack(anchor=tk.W, pady=(0, 8))

        self.lat_var = tk.StringVar(value="48.8566")
        self.lon_var = tk.StringVar(value="2.3522")
        self.radius_var = tk.StringVar(value="1.0")
        self.client_id_var = tk.StringVar()
        self.client_secret_var = tk.StringVar()
        self.compass_mode_var = tk.BooleanVar(value=False)
        self.battery_mode_var = tk.BooleanVar(value=False)
        self.scanline_var = tk.BooleanVar(value=True)
        self.triangles_var = tk.BooleanVar(value=True)
        self.info_var = tk.BooleanVar(value=False)
        self.heading_var = tk.DoubleVar(value=0.0)
        self.location_label_var = tk.StringVar(value="Position manuelle")

        self._add_entry(right, "Latitude", self.lat_var)
        self._add_entry(right, "Longitude", self.lon_var)
        self._add_entry(right, "Rayon (°)", self.radius_var)
        self._add_entry(right, "OpenSky Client ID", self.client_id_var)
        self._add_entry(right, "OpenSky Client Secret", self.client_secret_var, show="*")

        ttk.Label(right, textvariable=self.location_label_var).pack(anchor=tk.W, pady=(8, 4))

        btn_row = ttk.Frame(right)
        btn_row.pack(fill=tk.X, pady=4)
        ttk.Button(btn_row, text="Ma position (IP)", command=self._use_ip_location).pack(side=tk.LEFT)
        ttk.Button(btn_row, text="Rafraîchir", command=self._fetch_now).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_row, text="Sauvegarder", command=self._save_config).pack(side=tk.LEFT)

        checks = ttk.LabelFrame(right, text="Options", padding=8)
        checks.pack(fill=tk.X, pady=10)
        for text, var in [
            ("Rotation boussole", self.compass_mode_var),
            ("Mode batterie", self.battery_mode_var),
            ("Ligne de balayage", self.scanline_var),
            ("Triangles directionnels", self.triangles_var),
            ("Infos avion", self.info_var),
        ]:
            ttk.Checkbutton(checks, text=text, variable=var, command=self._apply_settings_to_engine).pack(anchor=tk.W)

        heading_frame = ttk.LabelFrame(right, text="Cap simulé (°)", padding=8)
        heading_frame.pack(fill=tk.X, pady=6)
        ttk.Scale(
            heading_frame,
            from_=0,
            to=359,
            orient=tk.HORIZONTAL,
            variable=self.heading_var,
            command=lambda _v: self._apply_settings_to_engine(),
        ).pack(fill=tk.X)
        self.heading_label = ttk.Label(heading_frame, text="0°")
        self.heading_label.pack(anchor=tk.W)

        stats_frame = ttk.LabelFrame(right, text="Statut / fiabilité", padding=8)
        stats_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.stats_text = tk.Text(
            stats_frame,
            height=12,
            wrap=tk.WORD,
            bg="#0f172a",
            fg="#4ade80",
            insertbackground="#4ade80",
            relief=tk.FLAT,
        )
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        self.stats_text.configure(state=tk.DISABLED)

        hint = ttk.Label(
            right,
            text="Astuce : faites tourner le cap pour tester la rotation du radar.",
            wraplength=320,
        )
        hint.pack(anchor=tk.W, pady=(6, 0))

    def _add_entry(self, parent: ttk.Frame, label: str, variable: tk.StringVar, show: str | None = None) -> None:
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=3)
        ttk.Label(row, text=label, width=18).pack(side=tk.LEFT)
        entry = ttk.Entry(row, textvariable=variable, show=show)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        entry.bind("<FocusOut>", lambda _e: self._apply_settings_to_engine())

    def _apply_settings_to_engine(self) -> None:
        try:
            self.engine.latitude = float(self.lat_var.get())
            self.engine.longitude = float(self.lon_var.get())
            self.engine.radius_deg = max(0.000001, min(2.5, float(self.radius_var.get())))
        except ValueError:
            return

        self.engine.client.set_credentials(self.client_id_var.get(), self.client_secret_var.get())
        self.engine.compass_mode = self.compass_mode_var.get()
        self.engine.battery_mode = self.battery_mode_var.get()
        self.engine.show_scanline = self.scanline_var.get()
        self.engine.show_triangles = self.triangles_var.get()
        self.engine.show_info = self.info_var.get()
        self.engine.heading_deg = float(self.heading_var.get())
        self.heading_label.configure(text=f"{self.engine.heading_deg:.0f}°")

    def _load_config(self) -> None:
        if not CONFIG_PATH.exists():
            return
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return

        self.lat_var.set(str(data.get("latitude", self.lat_var.get())))
        self.lon_var.set(str(data.get("longitude", self.lon_var.get())))
        self.radius_var.set(str(data.get("radius", self.radius_var.get())))
        self.client_id_var.set(data.get("opensky_id", ""))
        self.client_secret_var.set(data.get("opensky_secret", ""))
        self.compass_mode_var.set(bool(data.get("compass_mode", False)))
        self.battery_mode_var.set(bool(data.get("battery_mode", False)))
        self.scanline_var.set(bool(data.get("scanline", True)))
        self.triangles_var.set(bool(data.get("triangles", True)))
        self.info_var.set(bool(data.get("info", False)))
        self.heading_var.set(float(data.get("heading", 0.0)))
        self.location_label_var.set(data.get("location_label", "Position manuelle"))

    def _save_config(self) -> None:
        self._apply_settings_to_engine()
        payload = {
            "latitude": self.engine.latitude,
            "longitude": self.engine.longitude,
            "radius": self.engine.radius_deg,
            "opensky_id": self.client_id_var.get(),
            "opensky_secret": self.client_secret_var.get(),
            "compass_mode": self.compass_mode_var.get(),
            "battery_mode": self.battery_mode_var.get(),
            "scanline": self.scanline_var.get(),
            "triangles": self.triangles_var.get(),
            "info": self.info_var.get(),
            "heading": self.engine.heading_deg,
            "location_label": self.location_label_var.get(),
        }
        CONFIG_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        messagebox.showinfo("Sauvegarde", f"Configuration enregistrée dans\n{CONFIG_PATH}")

    def _use_ip_location(self) -> None:
        def worker() -> None:
            try:
                lat, lon, label = geolocate_ip()
                self.after(0, lambda: self._set_location(lat, lon, label))
            except Exception as exc:
                self.after(0, lambda: messagebox.showerror("Géolocalisation", str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def _set_location(self, lat: float, lon: float, label: str) -> None:
        self.lat_var.set(f"{lat:.6f}")
        self.lon_var.set(f"{lon:.6f}")
        self.location_label_var.set(f"Position : {label}")
        self._apply_settings_to_engine()
        self._fetch_now()

    def _fetch_now(self) -> None:
        if self._busy:
            return
        self._busy = True
        self._apply_settings_to_engine()

        def worker() -> None:
            stats = self.engine.update(force=True)
            self.after(0, lambda: self._on_fetch_done(stats))

        threading.Thread(target=worker, daemon=True).start()

    def _on_fetch_done(self, stats) -> None:
        self._busy = False
        self._update_stats(stats)

    def _tick(self) -> None:
        if not self._busy and self.engine.should_fetch(self.engine.now_ms()):
            self._fetch_now()
        else:
            self._draw_frame()
            self._update_stats(self.engine.build_stats(self.engine.now_ms()))
        self.after(50, self._tick)

    def _update_stats(self, stats) -> None:
        auth = "authentifié" if self.client_id_var.get() and self.client_secret_var.get() else "anonyme"
        lines = [
            f"Avions en vol : {stats.aircraft_in_air}",
            f"Total suivi : {stats.aircraft_total}",
            f"API : {'OK' if stats.last_fetch_ok else 'ERREUR'} ({stats.last_fetch_ms:.0f} ms)",
            f"Mode : {auth}",
            f"Intervalle : {stats.fetch_interval_s:.0f} s",
            f"Prochain fetch : {stats.next_fetch_in_s:.0f} s",
            "",
            stats.reliability_hint,
        ]
        if stats.last_error:
            lines.insert(4, f"Erreur : {stats.last_error}")

        self.stats_text.configure(state=tk.NORMAL)
        self.stats_text.delete("1.0", tk.END)
        self.stats_text.insert("1.0", "\n".join(lines))
        self.stats_text.configure(state=tk.DISABLED)

    def _draw_frame(self) -> None:
        self.canvas.delete("all")
        cx = cy = CANVAS_SIZE // 2
        outer = CANVAS_SIZE // 2 - 2

        for factor, color in [(1.0, "#00c800"), (2 / 3, "#004000"), (1 / 3, "#002000")]:
            r = outer * factor
            self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=color, width=2)

        if self.engine.show_scanline:
            if self.engine.compass_mode:
                angle = math.radians(self.engine.heading_deg)
            else:
                self._scan_phase += 0.02
                angle = self._scan_phase
            ex = cx + math.cos(angle) * outer
            ey = cy + math.sin(angle) * outer
            self.canvas.create_line(cx, cy, ex, ey, fill="#00c800", width=2)

        now_ms = self.engine.now_ms()
        for tracked, x, y in self.engine.visible_aircraft(now_ms):
            sx = x * CANVAS_SCALE
            sy = y * CANVAS_SCALE

            if self.engine.show_triangles:
                points = self.engine.triangle_points(tracked, x, y)
                flat = [coord * CANVAS_SCALE for point in points for coord in point]
                self.canvas.create_polygon(flat, fill="#00ff00", outline="#00ff00")
            else:
                self.canvas.create_oval(sx - 4, sy - 4, sx + 4, sy + 4, fill="#00ff00", outline="#00ff00")

            if self.engine.show_info and tracked.state.callsign:
                self.canvas.create_text(
                    sx + 8,
                    sy - 8,
                    text=tracked.state.callsign.strip(),
                    fill="#008000",
                    anchor=tk.W,
                    font=("TkFixedFont", 9),
                )

        self.canvas.create_oval(cx - 3, cy - 3, cx + 3, cy + 3, fill="#00ff00", outline="#00ff00")


def main() -> None:
    app = MicroRadarApp()
    app.mainloop()


if __name__ == "__main__":
    main()
