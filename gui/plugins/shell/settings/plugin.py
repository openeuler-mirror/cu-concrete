# -*- coding: utf-8 -*-
"""插件入口: shell.settings"""
from __future__ import annotations
import sys
from pathlib import Path

_GUI_ROOT = Path(__file__).resolve().parents[3]
if str(_GUI_ROOT) not in sys.path:
    sys.path.insert(0, str(_GUI_ROOT))

from core.plugin_api import GuiPlugin

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from plugins._shared.gtk_helpers import make_page, make_button_row

class SettingsPlugin(GuiPlugin):
    def create_widget(self, parent):
        page, body = make_page("设置", "窗口尺寸等界面偏好")
        win = self.context.settings.setdefault("window", {})
        self.width_adj = Gtk.Adjustment(value=int(win.get("width", 1100)), lower=640, upper=3840, step_increment=10)
        self.height_adj = Gtk.Adjustment(value=int(win.get("height", 720)), lower=480, upper=2160, step_increment=10)
        body.pack_start(Gtk.Label(label="默认宽度", xalign=0), False, False, 0)
        body.pack_start(Gtk.SpinButton(adjustment=self.width_adj), False, False, 0)
        body.pack_start(Gtk.Label(label="默认高度", xalign=0), False, False, 0)
        body.pack_start(Gtk.SpinButton(adjustment=self.height_adj), False, False, 0)
        body.pack_start(make_button_row([("应用并保存", self._save)]), False, False, 0)
        return page
    def _save(self, _button):
        self.context.settings.setdefault("window", {})
        self.context.settings["window"]["width"] = int(self.width_adj.get_value())
        self.context.settings["window"]["height"] = int(self.height_adj.get_value())
        self.context.save_settings()
        self.context.event_bus.publish("status", message="设置已保存，下次启动生效")

