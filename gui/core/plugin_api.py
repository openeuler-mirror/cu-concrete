# -*- coding: utf-8 -*-
"""插件契约：宿主与插件之间的唯一稳定接口。"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class PluginMeta:
    """插件清单元数据（通常来自 plugin.yaml）。"""
    plugin_id: str
    name: str
    category: str
    description: str = ""
    order: int = 100
    entry: str = "plugin:Plugin"
    standalone: bool = True
    tags: list = field(default_factory=list)
    policy_name: str = ""
    department: int = 0


class GuiPlugin:
    """所有插件的基类。子类实现 create_widget。"""

    def __init__(self, meta: PluginMeta, context: Any = None) -> None:
        self.meta: PluginMeta = meta
        self.context = context

    @property
    def plugin_id(self) -> str:
        return self.meta.plugin_id

    @property
    def name(self) -> str:
        return self.meta.name

    @property
    def category(self) -> str:
        return self.meta.category

    def create_widget(self, parent: Any) -> Any:
        raise NotImplementedError("插件必须实现 create_widget")

    def on_activate(self) -> None:
        return None

    def on_deactivate(self) -> None:
        return None

    def run_standalone(self) -> int:
        """独立窗口运行，返回进程退出码。"""
        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk
        window = Gtk.Window(title=self.meta.name)
        window.set_default_size(800, 600)
        window.connect("destroy", Gtk.main_quit)
        widget = self.create_widget(window)
        window.add(widget)
        self.on_activate()
        window.show_all()
        Gtk.main()
        self.on_deactivate()
        return 0
