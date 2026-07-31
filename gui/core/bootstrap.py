# -*- coding: utf-8 -*-
"""启动装配。"""
from __future__ import annotations
import logging
from pathlib import Path
from typing import Optional
from .app_context import AppContext
from .plugin_loader import PluginLoader
from .plugin_registry import PluginRegistry


def create_context(gui_root: Optional[Path] = None) -> AppContext:
    return AppContext(gui_root=gui_root)


def load_registry(context: AppContext) -> PluginRegistry:
    registry = PluginRegistry()
    loader = PluginLoader(context.gui_root / "plugins", context)
    loader.load_all(registry)
    context.extras["loader_errors"] = loader.errors
    return registry


def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
