"""Shared KivyMD styling and safe Android header widgets."""

from __future__ import annotations

from kivy.metrics import dp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel

# Palette
BG_DARK = (0.07, 0.09, 0.15, 1)
BG_STATS = (0.06, 0.09, 0.16, 1)
RADAR_BG = (0, 0, 0, 1)
ACCENT = (0.13, 0.77, 0.37, 1)
STATUS_OK = (0.29, 0.87, 0.5, 1)


def app_header(title: str = "Micro Radar") -> MDBoxLayout:
    """Safe title bar for Android (plain box layout, not KivyMD toolbar)."""
    bar = MDBoxLayout(
        orientation="horizontal",
        size_hint_y=None,
        height=dp(56),
        md_bg_color=BG_DARK,
        padding=(dp(16), dp(14)),
    )
    bar.add_widget(
        MDLabel(
            text=title,
            font_style="H6",
            theme_text_color="Primary",
            valign="center",
        )
    )
    return bar


def section_card(height: int, *, bg: tuple[float, float, float, float] = BG_DARK) -> MDCard:
    return MDCard(
        orientation="vertical",
        padding=dp(12),
        spacing=dp(8),
        size_hint_y=None,
        height=dp(height),
        md_bg_color=bg,
    )


def accent_button(text: str, on_release) -> MDRaisedButton:
    return MDRaisedButton(text=text, md_bg_color=ACCENT, on_release=on_release)
