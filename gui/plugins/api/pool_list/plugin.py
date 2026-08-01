# -*- coding: utf-8 -*-
"""插件入口: api.pool_list"""
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
import json

class PoolListPlugin(GuiPlugin):
    def create_widget(self, parent):
        page, body = make_page("云池列表", "经 ApiClientAdapter.list_pools")
        self.scroll, self.view = make_text_view("")
        body.pack_start(self.scroll, True, True, 0)
        body.pack_start(make_button_row([("刷新", self._reload)]), False, False, 0)
        self._reload(None)
        return page
    def _reload(self, _b):
        result = self.context.extras["api_adapter"].list_pools()
        self.view.get_buffer().set_text(json.dumps({"ok": result.ok, "message": result.message, "data": result.data}, ensure_ascii=False, indent=2))

