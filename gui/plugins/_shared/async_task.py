# -*- coding: utf-8 -*-
"""在后台线程执行耗时操作，避免卡住 GTK 主循环。"""
from __future__ import annotations
import threading
import traceback
from typing import Any, Callable, Optional
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GLib


def run_in_background(
    work: Callable[[], Any],
    on_success: Optional[Callable[[Any], None]] = None,
    on_error: Optional[Callable[[BaseException, str], None]] = None,
    on_done: Optional[Callable[[], None]] = None,
) -> None:
    """在守护线程中执行 work，结果通过 GLib.idle_add 回主线程。"""

    def runner() -> None:
        try:
            result = work()
        except BaseException as exc:  # noqa: BLE001
            tb = traceback.format_exc()

            def report_error() -> bool:
                if on_error is not None:
                    on_error(exc, tb)
                if on_done is not None:
                    on_done()
                return False

            GLib.idle_add(report_error)
            return

        def report_success() -> bool:
            if on_success is not None:
                on_success(result)
            if on_done is not None:
                on_done()
            return False

        GLib.idle_add(report_success)

    thread = threading.Thread(target=runner, name="gui-bg-task", daemon=True)
    thread.start()
