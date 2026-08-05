# -*- coding: utf-8 -*-
"""插件入口: shell.progress"""
from __future__ import annotations
import sys
from pathlib import Path

_GUI_ROOT = Path(__file__).resolve().parents[3]
if str(_GUI_ROOT) not in sys.path:
    sys.path.insert(0, str(_GUI_ROOT))

from core.plugin_api import GuiPlugin

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
from plugins._shared.gtk_helpers import make_page

class ProgressPlugin(GuiPlugin):
    def create_widget(self, parent):
        page, body = make_page("进度展示", "订阅 event_bus 的 progress 事件")
        self.bar = Gtk.ProgressBar()
        self.label = Gtk.Label(label="进度: 0%", xalign=0)
        body.pack_start(self.label, False, False, 0)
        body.pack_start(self.bar, False, False, 0)
        self.context.event_bus.subscribe("progress", self._on_progress)
        return page
    def _on_progress(self, fraction=0.0, **kwargs):
        def update():
            self.bar.set_fraction(float(fraction))
            self.label.set_text(f"进度: {int(float(fraction)*100)}%")
            return False
        GLib.idle_add(update)

