# -*- coding: utf-8 -*-
"""插件入口: shell.logs"""
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


class LogsPlugin(GuiPlugin):
    def create_widget(self, parent):
        page, body = make_page("日志", "查看 logs 目录下的日志文件")
        self.combo = Gtk.ComboBoxText()
        log_dir = self.context.repo_root / "logs"
        names = []
        if log_dir.is_dir():
            names = [path.name for path in sorted(log_dir.glob("*.log"))]
            for name in names:
                self.combo.append_text(name)
        if names:
            self.combo.set_active(0)
        else:
            self.combo.append_text("(无 .log 文件)")
            self.combo.set_active(0)
        self.combo.connect("changed", lambda *_: self._reload(None))
        body.pack_start(self.combo, False, False, 0)
        body.pack_start(make_button_row([("刷新", self._reload)]), False, False, 0)
        self.scroll, self.view = make_text_view("")
        body.pack_start(self.scroll, True, True, 0)
        self._reload(None)
        return page

    def _reload(self, _button):
        name = self.combo.get_active_text()
        log_dir = self.context.repo_root / "logs"
        if not name or name.startswith("("):
            self.view.get_buffer().set_text("暂无日志文件\n可在项目 logs/ 目录放入 *.log")
            return
        path = log_dir / name
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            if not text.strip():
                text = "(日志文件为空)"
        except Exception as exc:
            text = f"读取失败: {exc}"
        self.view.get_buffer().set_text(text[-200000:])
        if self.context:
            self.context.event_bus.publish("status", message=f"已加载日志 {name}")
