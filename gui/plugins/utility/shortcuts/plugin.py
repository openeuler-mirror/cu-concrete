# -*- coding: utf-8 -*-
"""插件入口: utility.shortcuts"""
from __future__ import annotations
import sys
from pathlib import Path

_GUI_ROOT = Path(__file__).resolve().parents[3]
if str(_GUI_ROOT) not in sys.path:
    sys.path.insert(0, str(_GUI_ROOT))

from core.plugin_api import GuiPlugin

from plugins._shared.gtk_helpers import make_page, make_text_view

class ShortcutsPlugin(GuiPlugin):
    def create_widget(self, parent):
        page, body = make_page("快捷键说明", "当前版本以鼠标操作为主")
        text = (
            "主界面:\n"
            "- 左侧点击插件切换功能\n"
            "- 顶栏「帮助」打开帮助中心\n"
            "- 顶栏「刷新列表」重建侧栏\n\n"
            "命令行:\n"
            "- python3 gui/main.py\n"
            "- python3 gui/main.py --list\n"
            "- python3 gui/main.py --plugin <id>\n"
        )
        scroll, _ = make_text_view(text)
        body.pack_start(scroll, True, True, 0)
        return page

