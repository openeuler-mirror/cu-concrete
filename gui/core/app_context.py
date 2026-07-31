# -*- coding: utf-8 -*-
"""应用上下文：路径、事件、设置、适配器。"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Any, Optional
import yaml
from .event_bus import EventBus


class AppContext:
    def __init__(self, gui_root: Optional[Path] = None) -> None:
        self.gui_root: Path = gui_root or Path(__file__).resolve().parent.parent
        self.repo_root: Path = self.gui_root.parent
        self.event_bus: EventBus = EventBus()
        self.settings: dict = self._load_settings()
        self.extras: dict = {}

    def _load_settings(self) -> dict:
        path = self.gui_root / "config" / "gui_settings.yaml"
        if not path.exists():
            return {}
        with open(path, "r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}

    def save_settings(self) -> None:
        path = self.gui_root / "config" / "gui_settings.yaml"
        with open(path, "w", encoding="utf-8") as handle:
            yaml.safe_dump(self.settings, handle, allow_unicode=True)

    def path(self, *parts: str) -> Path:
        return self.repo_root.joinpath(*parts)
