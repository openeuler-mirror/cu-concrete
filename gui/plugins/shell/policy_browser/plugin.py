# -*- coding: utf-8 -*-
"""插件入口: shell.policy_browser"""
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

class PolicyBrowserPlugin(GuiPlugin):
    def create_widget(self, parent):
        page, body = make_page("策略浏览", "按部门展示策略元数据（经 DepartmentAdapter）")
        store = Gtk.ListStore(int, str, str, str)
        dept = self.context.extras["department_adapter"]
        for info in self.context.extras["policy_adapter"].list_items():
            store.append([info.department, info.name, info.description, info.module_path])
        tree = Gtk.TreeView(model=store)
        for i, title in enumerate(["部门", "名称", "描述", "路径"]):
            tree.append_column(Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=i))
        scroll = Gtk.ScrolledWindow()
        scroll.add(tree)
        scroll.set_vexpand(True)
        body.pack_start(scroll, True, True, 0)
        return page

