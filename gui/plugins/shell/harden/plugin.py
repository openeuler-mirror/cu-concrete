# -*- coding: utf-8 -*-
"""插件入口: shell.harden"""
from __future__ import annotations
import sys
from pathlib import Path

_GUI_ROOT = Path(__file__).resolve().parents[3]
if str(_GUI_ROOT) not in sys.path:
    sys.path.insert(0, str(_GUI_ROOT))

from core.plugin_api import GuiPlugin

from plugins._shared.action_panel import ActionPanel

class HardenPlugin(GuiPlugin):
    def create_widget(self, parent):
        adapter = self.context.extras["policy_adapter"]
        names = [i.name for i in adapter.list_items()]
        def run_selected(selected):
            lines = []
            total = len(selected) or 1
            for idx, name in enumerate(selected, 1):
                result = adapter.harden(name)
                lines.append(f"[{idx}/{total}] {name}: {'OK' if result.ok else 'FAIL'} - {result.message}")
                if self.context:
                    self.context.event_bus.publish("progress", fraction=idx / total)
            text = "\n".join(lines)
            if self.context:
                self.context.event_bus.publish("result", message=text)
            return text
        return ActionPanel("加固", "选择策略项并执行加固（经 PolicyAdapter 转调 fix）", names, lambda n: "", run_selected, self.context)

