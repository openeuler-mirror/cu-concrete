# -*- coding: utf-8 -*-
"""插件入口: shell.about"""
from __future__ import annotations
import sys
from pathlib import Path

_GUI_ROOT = Path(__file__).resolve().parents[3]
if str(_GUI_ROOT) not in sys.path:
    sys.path.insert(0, str(_GUI_ROOT))

from core.plugin_api import GuiPlugin

from plugins._shared.gtk_helpers import make_page, make_text_view

class AboutPlugin(GuiPlugin):
    def create_widget(self, parent):
        page, body = make_page("关于", "cu-concrete GTK3 插件化 GUI")
        text = (
            "cu-concrete GUI\n"
            "技术栈: Python3 + PyGObject/GTK3\n"
            "架构: 约定目录扫描插件 + 适配器转调现有策略\n"
            "入口: python3 gui/main.py\n"
            "本模块独立于 TUI/CLI，不修改原有业务源码。\n"
        )
        scroll, _ = make_text_view(text)
        body.pack_start(scroll, True, True, 0)
        return page

