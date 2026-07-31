# -*- coding: utf-8 -*-
"""插件注册表。"""
from __future__ import annotations
from typing import Dict, List, Optional
from .plugin_api import GuiPlugin


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: Dict[str, GuiPlugin] = {}

    def register(self, plugin: GuiPlugin) -> None:
        self._plugins[plugin.plugin_id] = plugin

    def get(self, plugin_id: str) -> Optional[GuiPlugin]:
        return self._plugins.get(plugin_id)

    def all(self) -> List[GuiPlugin]:
        return sorted(self._plugins.values(), key=lambda p: (p.category, p.meta.order, p.plugin_id))

    def by_category(self, category: str) -> List[GuiPlugin]:
        return [p for p in self.all() if p.category == category]

    def categories(self) -> List[str]:
        order = ["shell", "policy", "api", "utility"]
        found = sorted({p.category for p in self._plugins.values()})
        return [c for c in order if c in found] + [c for c in found if c not in order]

    def ids(self) -> List[str]:
        return [p.plugin_id for p in self.all()]
