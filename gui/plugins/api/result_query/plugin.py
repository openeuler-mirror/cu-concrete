# -*- coding: utf-8 -*-
"""插件入口: api.result_query"""
from __future__ import annotations
import sys
from pathlib import Path

_GUI_ROOT = Path(__file__).resolve().parents[3]
if str(_GUI_ROOT) not in sys.path:
    sys.path.insert(0, str(_GUI_ROOT))

from core.plugin_api import GuiPlugin

import json
from plugins._shared.gtk_helpers import make_page, make_button_row, make_text_view

class ResultQueryPlugin(GuiPlugin):
    def create_widget(self, parent):
        page, body = make_page("结果查询", "经 ApiClientAdapter.list_results")
        self.scroll, self.view = make_text_view("")
        body.pack_start(self.scroll, True, True, 0)
        body.pack_start(make_button_row([("刷新", self._load)]), False, False, 0)
        self._load(None)
        return page
    def _load(self, _b):
        result = self.context.extras["api_adapter"].list_results()
        self.view.get_buffer().set_text(json.dumps({"ok": result.ok, "message": result.message, "data": result.data}, ensure_ascii=False, indent=2))

