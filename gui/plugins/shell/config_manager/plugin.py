# -*- coding: utf-8 -*-
"""插件入口: shell.config_manager"""
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
from plugins._shared.gtk_helpers import make_page, make_button_row, make_text_view
import yaml

class ConfigManagerPlugin(GuiPlugin):
    def create_widget(self, parent):
        page, body = make_page("配置管理", "编辑 gui/config/gui_settings.yaml")
        self.scroll, self.view = make_text_view("")
        self.view.set_editable(True)
        body.pack_start(self.scroll, True, True, 0)
        body.pack_start(make_button_row([("重新加载", self._load), ("保存", self._save)]), False, False, 0)
        self._load(None)
        return page
    def _load(self, _button):
        path = self.context.gui_root / "config" / "gui_settings.yaml"
        self.view.get_buffer().set_text(path.read_text(encoding="utf-8") if path.exists() else "")
    def _save(self, _button):
        buffer = self.view.get_buffer()
        text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)
        path = self.context.gui_root / "config" / "gui_settings.yaml"
        # 校验 yaml
        yaml.safe_load(text)
        path.write_text(text, encoding="utf-8")
        self.context.settings = yaml.safe_load(text) or {}
        self.context.event_bus.publish("status", message="GUI 配置已保存")

