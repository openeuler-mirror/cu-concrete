# -*- coding: utf-8 -*-
"""插件入口: utility.help_center"""
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
from plugins._shared.gtk_helpers import make_page, make_text_view

class HelpCenterPlugin(GuiPlugin):
    def create_widget(self, parent):
        page, body = make_page("帮助中心", "浏览各插件 README")
        self.store = Gtk.ListStore(str, str)
        plugins_root = self.context.gui_root / "plugins"
        for readme in sorted(plugins_root.rglob("README.md")):
            if "_shared" in readme.parts:
                continue
            self.store.append([str(readme.relative_to(plugins_root)), str(readme)])
        tree = Gtk.TreeView(model=self.store)
        tree.append_column(Gtk.TreeViewColumn("文档", Gtk.CellRendererText(), text=0))
        tree.get_selection().connect("changed", self._on_select)
        scroll = Gtk.ScrolledWindow()
        scroll.set_size_request(-1, 180)
        scroll.add(tree)
        body.pack_start(scroll, False, False, 0)
        self.doc_scroll, self.doc_view = make_text_view("选择左侧文档")
        body.pack_start(self.doc_scroll, True, True, 0)
        return page
    def _on_select(self, selection):
        model, it = selection.get_selected()
        if not it:
            return
        path = Path(model[it][1])
        try:
            self.doc_view.get_buffer().set_text(path.read_text(encoding="utf-8"))
        except Exception as exc:
            self.doc_view.get_buffer().set_text(str(exc))

