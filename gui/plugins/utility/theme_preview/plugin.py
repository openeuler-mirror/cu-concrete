# -*- coding: utf-8 -*-
"""插件入口: utility.theme_preview"""
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
from plugins._shared.gtk_helpers import make_page

class ThemePreviewPlugin(GuiPlugin):
    def create_widget(self, parent):
        page, body = make_page("主题预览", "仅用于观察控件样式")
        body.pack_start(Gtk.Entry(), False, False, 0)
        body.pack_start(Gtk.CheckButton(label="示例复选框"), False, False, 0)
        body.pack_start(Gtk.Button(label="示例按钮"), False, False, 0)
        switch = Gtk.Switch()
        body.pack_start(switch, False, False, 0)
        return page

