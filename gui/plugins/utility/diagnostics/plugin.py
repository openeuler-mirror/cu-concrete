# -*- coding: utf-8 -*-
"""插件入口: utility.diagnostics"""
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

class DiagnosticsPlugin(GuiPlugin):
    def create_widget(self, parent):
        page, body = make_page("环境自检", "快速确认 GUI 运行环境")
        self.scroll, self.view = make_text_view("")
        body.pack_start(self.scroll, True, True, 0)
        body.pack_start(make_button_row([("开始自检", self._run)]), False, False, 0)
        self._run(None)
        return page
    def _run(self, _b):
        lines = []
        lines.append(f"GUI_ROOT={self.context.gui_root}")
        lines.append(f"REPO_ROOT={self.context.repo_root}")
        try:
            from gi.repository import Gtk as G
            lines.append(f"GTK major={G.get_major_version()} minor={G.get_minor_version()}")
        except Exception as exc:
            lines.append(f"GTK 异常: {exc}")
        for dept in (1, 2):
            p = self.context.repo_root / f"department_{dept}_policy"
            lines.append(f"{p.name} exists={p.is_dir()}")
        items = self.context.extras["policy_adapter"].list_items()
        lines.append(f"策略项扫描数量={len(items)}")
        manifests = list((self.context.gui_root / "plugins").rglob("plugin.yaml"))
        lines.append(f"插件清单数量={len(manifests)}")
        errs = self.context.extras.get("loader_errors") or []
        lines.append(f"最近加载错误数={len(errs)}")
        self.view.get_buffer().set_text("\n".join(lines))

