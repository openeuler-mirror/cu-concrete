# -*- coding: utf-8 -*-
"""批量策略操作面板（后台执行，不阻塞界面）。"""
from __future__ import annotations
from typing import Any, Callable, List
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from .gtk_helpers import make_page, make_button_row, make_text_view, append_text
from .async_task import run_in_background


class ActionPanel(Gtk.Box):
    def __init__(
        self,
        title: str,
        subtitle: str,
        item_names: List[str],
        on_run_one: Callable[[str], str],
        on_run_selected: Callable[[List[str]], str],
        context: Any = None,
    ) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        page, body = make_page(title, subtitle)
        self.pack_start(page, True, True, 0)
        self.context = context
        self.on_run_one = on_run_one
        self.on_run_selected = on_run_selected
        self._busy = False
        self.list_store = Gtk.ListStore(bool, str)
        for name in item_names:
            self.list_store.append([False, name])
        tree = Gtk.TreeView(model=self.list_store)
        toggle = Gtk.CellRendererToggle()
        toggle.set_activatable(True)
        toggle.connect("toggled", self._on_toggle)
        tree.append_column(Gtk.TreeViewColumn("选择", toggle, active=0))
        tree.append_column(Gtk.TreeViewColumn("策略", Gtk.CellRendererText(), text=1))
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.add(tree)
        body.pack_start(scroll, True, True, 0)
        self.run_button = Gtk.Button(label="执行选中")
        self.run_button.connect("clicked", self._run_selected)
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        for text, callback in (("全选", self._select_all), ("清空", self._clear_all)):
            button = Gtk.Button(label=text)
            button.connect("clicked", callback)
            row.pack_start(button, False, False, 0)
        row.pack_start(self.run_button, False, False, 0)
        body.pack_start(row, False, False, 0)
        self.log_scroll, self.log_view = make_text_view("等待操作...\n")
        body.pack_start(self.log_scroll, True, True, 0)

    def _on_toggle(self, _widget: Gtk.CellRendererToggle, path: str) -> None:
        self.list_store[path][0] = not self.list_store[path][0]

    def _select_all(self, _button: Gtk.Button) -> None:
        for row in self.list_store:
            row[0] = True

    def _clear_all(self, _button: Gtk.Button) -> None:
        for row in self.list_store:
            row[0] = False

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.run_button.set_sensitive(not busy)
        self.run_button.set_label("执行中..." if busy else "执行选中")

    def _run_selected(self, _button: Gtk.Button) -> None:
        if self._busy:
            append_text(self.log_view, "已有任务在执行，请稍候")
            return
        selected = [row[1] for row in self.list_store if row[0]]
        if not selected:
            append_text(self.log_view, "未选择任何项")
            return
        if self.context is not None:
            self.context.event_bus.publish("status", message=f"后台执行 {len(selected)} 项...")
            self.context.event_bus.publish("progress", fraction=0.05)
        self._set_busy(True)
        append_text(self.log_view, f"开始执行 {len(selected)} 项（后台）...")

        def work() -> str:
            return self.on_run_selected(selected)

        def on_success(message: str) -> None:
            append_text(self.log_view, message or "(无输出)")
            if self.context is not None:
                self.context.event_bus.publish("progress", fraction=1.0)
                self.context.event_bus.publish("status", message="批量操作完成")
                self.context.event_bus.publish("result", message=message)

        def on_error(exc: BaseException, tb: str) -> None:
            append_text(self.log_view, f"执行失败: {exc}\n{tb}")
            if self.context is not None:
                self.context.event_bus.publish("status", message=f"执行失败: {exc}")

        def on_done() -> None:
            self._set_busy(False)

        run_in_background(work, on_success=on_success, on_error=on_error, on_done=on_done)
