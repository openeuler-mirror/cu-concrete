# -*- coding: utf-8 -*-
"""单策略详情面板：检查/加固/还原/修复，后台执行。"""
from __future__ import annotations
from typing import Any, Callable
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from .gtk_helpers import make_page, make_text_view, append_text
from .async_task import run_in_background


class PolicyDetailPanel(Gtk.Box):
    def __init__(self, title: str, subtitle: str, policy_name: str, department: int, context: Any) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        page, body = make_page(title, subtitle)
        self.pack_start(page, True, True, 0)
        self.context = context
        self.policy_name = policy_name
        self._busy = False
        info = Gtk.Label(label=f"策略: {policy_name} / 部门: {department}", xalign=0)
        body.pack_start(info, False, False, 0)
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.buttons = {}
        for key, label in (
            ("check", "检查 check"),
            ("harden", "加固 fix"),
            ("restore", "还原 rollback"),
            ("repair", "修复 reset"),
        ):
            button = Gtk.Button(label=label)
            button.connect("clicked", self._make_handler(key))
            row.pack_start(button, False, False, 0)
            self.buttons[key] = button
        body.pack_start(row, False, False, 0)
        self.scroll, self.view = make_text_view("等待操作...\n")
        body.pack_start(self.scroll, True, True, 0)

    def _make_handler(self, action: str) -> Callable:
        def handler(_button: Gtk.Button) -> None:
            self._run_action(action)
        return handler

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        for button in self.buttons.values():
            button.set_sensitive(not busy)

    def _run_action(self, action: str) -> None:
        if self._busy:
            append_text(self.view, "已有任务在执行，请稍候")
            return
        adapter = self.context.extras["policy_adapter"]
        mapping = {
            "check": adapter.check,
            "harden": adapter.harden,
            "restore": adapter.restore,
            "repair": adapter.repair,
        }
        method = mapping[action]
        self._set_busy(True)
        append_text(self.view, f"开始 {action}（后台）...")
        if self.context is not None:
            self.context.event_bus.publish("status", message=f"{self.policy_name}: {action} 进行中")
            self.context.event_bus.publish("progress", fraction=0.1)

        def work():
            return method(self.policy_name)

        def on_success(result) -> None:
            text = f"ok={result.ok} | {result.message} | data={result.data}"
            append_text(self.view, text)
            if self.context is not None:
                self.context.event_bus.publish("result", message=f"{self.policy_name}: {text}")
                self.context.event_bus.publish("status", message=f"{self.policy_name}: {result.message}")
                self.context.event_bus.publish("progress", fraction=1.0)

        def on_error(exc: BaseException, tb: str) -> None:
            append_text(self.view, f"失败: {exc}\n{tb}")
            if self.context is not None:
                self.context.event_bus.publish("status", message=f"{self.policy_name}: 失败 {exc}")

        def on_done() -> None:
            self._set_busy(False)

        run_in_background(work, on_success=on_success, on_error=on_error, on_done=on_done)
