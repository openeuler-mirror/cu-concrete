#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cu-concrete GUI 唯一入口。

用法:
  python3 gui/main.py
  python3 gui/main.py --list
  python3 gui/main.py --plugin shell.harden
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

GUI_ROOT = Path(__file__).resolve().parent
REPO_ROOT = GUI_ROOT.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(GUI_ROOT) not in sys.path:
    sys.path.insert(0, str(GUI_ROOT))


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="cu-concrete GTK3 插件化 GUI")
    parser.add_argument("--list", action="store_true", help="列出全部插件后退出")
    parser.add_argument("--plugin", type=str, default="", help="仅运行指定插件 id")
    parser.add_argument("-v", "--verbose", action="store_true", help="调试日志")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    from core.bootstrap import create_context, load_registry, setup_logging
    import logging
    setup_logging(logging.DEBUG if args.verbose else logging.INFO)
    context = create_context(GUI_ROOT)
    # 预挂适配器，供插件使用
    from adapters.policy_adapter import PolicyAdapter
    from adapters.department_adapter import DepartmentAdapter
    from adapters.api_client_adapter import ApiClientAdapter
    context.extras["policy_adapter"] = PolicyAdapter(REPO_ROOT)
    context.extras["department_adapter"] = DepartmentAdapter(REPO_ROOT)
    context.extras["api_adapter"] = ApiClientAdapter(REPO_ROOT)
    registry = load_registry(context)
    if args.list:
        for plugin in registry.all():
            print(f"{plugin.plugin_id:40s} [{plugin.category}] {plugin.name}")
        if context.extras.get("loader_errors"):
            print(f"\n加载失败: {len(context.extras['loader_errors'])} 个", file=sys.stderr)
        return 0
    if args.plugin:
        plugin = registry.get(args.plugin)
        if plugin is None:
            print(f"未找到插件: {args.plugin}", file=sys.stderr)
            print("可用插件:", ", ".join(registry.ids()), file=sys.stderr)
            return 1
        return plugin.run_standalone()
    import gi
    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk
    from core.main_window import MainWindow
    window = MainWindow(context, registry)
    last = context.settings.get("last_plugin") or ""
    if last and registry.get(last):
        window.show_plugin(last)
    window.show_all()
    Gtk.main()
    try:
        context.save_settings()
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
