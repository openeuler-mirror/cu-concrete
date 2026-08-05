# -*- coding: utf-8 -*-
"""插件入口: shell.results"""
from __future__ import annotations
import sys
from pathlib import Path

_GUI_ROOT = Path(__file__).resolve().parents[3]
if str(_GUI_ROOT) not in sys.path:
    sys.path.insert(0, str(_GUI_ROOT))

from core.plugin_api import GuiPlugin

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GLib
from plugins._shared.gtk_helpers import make_page, make_text_view, append_text

class ResultsPlugin(GuiPlugin):
    def create_widget(self, parent):
        page, body = make_page("结果展示", "订阅 event_bus 的 result 事件")
        self.scroll, self.view = make_text_view("尚无结果\n")
        body.pack_start(self.scroll, True, True, 0)
        self.context.event_bus.subscribe("result", self._on_result)
        return page
    def _on_result(self, message="", **kwargs):
        GLib.idle_add(append_text, self.view, message or "(空结果)")

