# -*- coding: utf-8 -*-
"""插件入口: api.task_run"""
from __future__ import annotations
import sys
from pathlib import Path

_GUI_ROOT = Path(__file__).resolve().parents[3]
if str(_GUI_ROOT) not in sys.path:
    sys.path.insert(0, str(_GUI_ROOT))

from core.plugin_api import GuiPlugin

import json
from plugins._shared.gtk_helpers import make_page, make_button_row, make_text_view

class TaskRunPlugin(GuiPlugin):
    def create_widget(self, parent):
        page, body = make_page("任务执行", "本地预览 conf_harden；实际远端任务可后续接 HTTP")
        self.scroll, self.view = make_text_view("")
        body.pack_start(self.scroll, True, True, 0)
        body.pack_start(make_button_row([("读取 conf_harden", self._load)]), False, False, 0)
        self._load(None)
        return page
    def _load(self, _b):
        result = self.context.extras["api_adapter"].read_conf_harden()
        self.view.get_buffer().set_text(json.dumps({"ok": result.ok, "message": result.message, "data": result.data}, ensure_ascii=False, indent=2, default=str))

