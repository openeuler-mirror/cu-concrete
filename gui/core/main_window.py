# -*- coding: utf-8 -*-
"""主窗口：分类列表 + 插件内容区。"""
from __future__ import annotations
from typing import Any, Dict, Optional
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
from .plugin_registry import PluginRegistry
from .app_context import AppContext

CATEGORY_LABELS = {
    "shell": "主功能",
    "policy": "策略项",
    "api": "API",
    "utility": "配套工具",
}


class MainWindow(Gtk.Window):
    def __init__(self, context: AppContext, registry: PluginRegistry) -> None:
        super().__init__(title="cu-concrete GUI")
        self.context = context
        self.registry = registry
        self._current_plugin_id: Optional[str] = None
        self._plugin_widgets: Dict[str, Gtk.Widget] = {}
        width = int(context.settings.get("window", {}).get("width", 1100))
        height = int(context.settings.get("window", {}).get("height", 720))
        self.set_default_size(width, height)
        self.connect("destroy", Gtk.main_quit)
        self._build_ui()
        context.event_bus.subscribe("status", self._on_status)
        context.event_bus.subscribe("progress", self._on_progress)

    def _build_ui(self) -> None:
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(root)
        header = Gtk.HeaderBar()
        header.set_show_close_button(True)
        header.props.title = "cu-concrete 安全加固"
        header.props.subtitle = "插件化 GUI"
        self.set_titlebar(header)
        refresh_btn = Gtk.Button(label="刷新列表")
        refresh_btn.connect("clicked", self._on_refresh)
        header.pack_end(refresh_btn)
        help_btn = Gtk.Button(label="帮助")
        help_btn.connect("clicked", self._on_help)
        header.pack_end(help_btn)
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        root.pack_start(paned, True, True, 0)
        self.sidebar = Gtk.TreeStore(str, str)  # display, plugin_id
        self.tree = Gtk.TreeView(model=self.sidebar)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("功能", renderer, text=0)
        self.tree.append_column(column)
        self.tree.get_selection().connect("changed", self._on_select)
        scroll_left = Gtk.ScrolledWindow()
        scroll_left.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll_left.add(self.tree)
        scroll_left.set_size_request(260, -1)
        paned.add1(scroll_left)
        self.content_stack = Gtk.Stack()
        self.content_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        placeholder = Gtk.Label(label="请从左侧选择功能插件")
        placeholder.set_name("placeholder")
        self.content_stack.add_named(placeholder, "placeholder")
        paned.add2(self.content_stack)
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        status_box.set_margin_start(8)
        status_box.set_margin_end(8)
        status_box.set_margin_top(4)
        status_box.set_margin_bottom(4)
        self.status_label = Gtk.Label(label="就绪", xalign=0)
        self.progress = Gtk.ProgressBar()
        self.progress.set_fraction(0.0)
        self.progress.set_size_request(180, -1)
        status_box.pack_start(self.status_label, True, True, 0)
        status_box.pack_end(self.progress, False, False, 0)
        root.pack_end(status_box, False, False, 0)
        self._fill_sidebar()

    def _fill_sidebar(self) -> None:
        self.sidebar.clear()
        for category in self.registry.categories():
            parent = self.sidebar.append(None, [CATEGORY_LABELS.get(category, category), ""])
            for plugin in self.registry.by_category(category):
                self.sidebar.append(parent, [plugin.name, plugin.plugin_id])
        self.tree.expand_all()

    def _on_select(self, selection: Gtk.TreeSelection) -> None:
        model, tree_iter = selection.get_selected()
        if tree_iter is None:
            return
        plugin_id = model[tree_iter][1]
        if not plugin_id:
            self.status_label.set_text("请展开分类并选择具体功能")
            return
        self.show_plugin(plugin_id)

    def show_plugin(self, plugin_id: str) -> None:
        plugin = self.registry.get(plugin_id)
        if plugin is None:
            self.status_label.set_text(f"未找到插件: {plugin_id}")
            return
        if self._current_plugin_id and self._current_plugin_id != plugin_id:
            old = self.registry.get(self._current_plugin_id)
            if old:
                old.on_deactivate()
        if plugin_id not in self._plugin_widgets:
            try:
                widget = plugin.create_widget(self)
            except Exception as exc:  # noqa: BLE001
                widget = self._build_error_widget(plugin_id, exc)
            self._plugin_widgets[plugin_id] = widget
            self.content_stack.add_named(widget, plugin_id)
            # 主窗 show_all 之后动态加入的子控件必须再 show，否则整页空白、点击无响应
            widget.show_all()
        self.content_stack.set_visible_child_name(plugin_id)
        visible = self.content_stack.get_visible_child()
        if visible is not None:
            visible.show_all()
        plugin.on_activate()
        self._current_plugin_id = plugin_id
        self.context.settings["last_plugin"] = plugin_id
        self.status_label.set_text(f"当前: {plugin.name}")

    def _build_error_widget(self, plugin_id: str, exc: Exception) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        label = Gtk.Label(label=f"插件加载界面失败: {plugin_id}")
        label.set_xalign(0)
        detail = Gtk.Label(label=str(exc))
        detail.set_xalign(0)
        detail.set_line_wrap(True)
        box.pack_start(label, False, False, 0)
        box.pack_start(detail, False, False, 0)
        return box

    def _on_refresh(self, _button: Gtk.Button) -> None:
        self._fill_sidebar()
        self.context.event_bus.publish("status", message="插件列表已刷新")

    def _on_help(self, _button: Gtk.Button) -> None:
        if self.registry.get("utility.help_center"):
            self.show_plugin("utility.help_center")

    def _on_status(self, message: str = "", **_kwargs: Any) -> None:
        GLib.idle_add(self.status_label.set_text, message or "就绪")

    def _on_progress(self, fraction: float = 0.0, **_kwargs: Any) -> None:
        GLib.idle_add(self.progress.set_fraction, max(0.0, min(1.0, float(fraction))))
