"""Shared GTK styling and process helpers for abzOS's Control Center and
Notification Center. Both are small always-launch-fresh popup apps (not
long-running daemons), styled to match the rest of the system: dark navy
cards, macOS system blue (#0A84FF) accent, JetBrains Mono for numbers/labels.
"""
import shutil
import subprocess

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, Gtk  # noqa: E402

CSS = b"""
window.abzos-panel {
    background-color: transparent;
}
box.abzos-card {
    background-color: rgba(16, 20, 30, 0.98);
    border-radius: 18px;
    border: 1px solid rgba(10, 132, 255, 0.18);
    padding: 16px;
}
button.abzos-pill {
    background-color: rgba(255, 255, 255, 0.06);
    background-image: none;
    border-radius: 14px;
    padding: 10px 14px;
    border: none;
    box-shadow: none;
    color: #f8f8f2;
    min-height: 44px;
}
button.abzos-pill:hover {
    background-color: rgba(255, 255, 255, 0.10);
}
button.abzos-pill.active {
    background-color: #0A84FF;
    color: #ffffff;
}
button.abzos-pill.active label,
button.abzos-pill.active .abzos-sub {
    color: #ffffff;
}
button.abzos-icon-btn {
    background-color: rgba(255, 255, 255, 0.06);
    background-image: none;
    border-radius: 999px;
    min-width: 36px;
    min-height: 36px;
    border: none;
    box-shadow: none;
    color: #f8f8f2;
    padding: 0;
}
button.abzos-icon-btn:hover {
    background-color: rgba(255, 255, 255, 0.14);
}
button.abzos-battery {
    background-color: rgba(255, 255, 255, 0.06);
    border-radius: 999px;
    border: none;
    box-shadow: none;
    color: #f8f8f2;
    padding: 6px 14px;
}
label.abzos-title {
    color: #f8f8f2;
    font-weight: bold;
}
label.abzos-sub {
    color: #8b949e;
    font-size: 90%;
}
label.abzos-heading {
    color: #f8f8f2;
    font-weight: bold;
    font-size: 110%;
}
scale.abzos-slider trough {
    background-color: rgba(255, 255, 255, 0.10);
    border-radius: 8px;
    min-height: 6px;
}
scale.abzos-slider highlight {
    background-color: #0A84FF;
    border-radius: 8px;
    min-height: 6px;
}
scale.abzos-slider slider {
    background-color: #ffffff;
    border-radius: 999px;
    min-width: 16px;
    min-height: 16px;
    margin: -6px;
}
box.abzos-row {
    padding: 4px 2px;
}
frame.abzos-frame {
    border: none;
}
calendar.abzos-calendar {
    background-color: transparent;
    color: #f8f8f2;
}
"""


def load_css():
    provider = Gtk.CssProvider()
    provider.load_from_data(CSS)
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )


def enable_transparency(window):
    screen = window.get_screen()
    visual = screen.get_rgba_visual()
    if visual is not None:
        window.set_visual(visual)
    window.set_app_paintable(True)


def run(cmd):
    """Fire-and-forget an external command."""
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def run_out(cmd, default="", timeout=1.5):
    """Run a command and return its stdout, or `default` on any failure or
    if it doesn't finish within `timeout` seconds (some tools, notably
    `bluetoothctl show` when bluetoothd isn't fully up yet, can hang
    indefinitely -- a status probe must never be allowed to block the UI)."""
    try:
        return subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True, timeout=timeout).strip()
    except Exception:
        return default


def has_cmd(name):
    return shutil.which(name) is not None


def position_top_right(window, width, margin_top=32, margin_right=12):
    screen = Gdk.Screen.get_default()
    monitor = screen.get_display().get_primary_monitor() or screen.get_display().get_monitor(0)
    geo = monitor.get_geometry()
    x = geo.x + geo.width - width - margin_right
    y = geo.y + margin_top
    window.move(x, y)


def position_top_center(window, width, margin_top=32):
    """Center under the top-bar clock, which itself sits at screen center."""
    screen = Gdk.Screen.get_default()
    monitor = screen.get_display().get_primary_monitor() or screen.get_display().get_monitor(0)
    geo = monitor.get_geometry()
    x = geo.x + (geo.width - width) // 2
    y = geo.y + margin_top
    window.move(x, y)
