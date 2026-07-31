# -*- coding: utf-8 -*-
"""约定目录扫描加载：plugins/**/plugin.yaml + plugin.py。"""
from __future__ import annotations
import importlib.util
import logging
import traceback
from pathlib import Path
from typing import Any, List, Tuple
import yaml
from .plugin_api import GuiPlugin, PluginMeta
from .plugin_registry import PluginRegistry

logger = logging.getLogger(__name__)


class PluginLoader:
    def __init__(self, plugins_root: Path, context: Any) -> None:
        self.plugins_root: Path = plugins_root
        self.context = context
        self.errors: List[Tuple[str, str]] = []

    def discover_manifests(self) -> List[Path]:
        if not self.plugins_root.exists():
            return []
        return sorted(self.plugins_root.rglob("plugin.yaml"))

    def load_all(self, registry: PluginRegistry) -> PluginRegistry:
        for manifest_path in self.discover_manifests():
            try:
                plugin = self._load_one(manifest_path)
                if plugin is not None:
                    registry.register(plugin)
            except Exception as exc:  # noqa: BLE001
                message = f"{manifest_path}: {exc}"
                self.errors.append((str(manifest_path), traceback.format_exc()))
                logger.error("插件加载失败: %s", message)
        return registry

    def _load_one(self, manifest_path: Path) -> GuiPlugin:
        with open(manifest_path, "r", encoding="utf-8") as handle:
            raw = yaml.safe_load(handle) or {}
        meta = PluginMeta(
            plugin_id=str(raw.get("id") or ""),
            name=str(raw.get("name") or meta_fallback_name(manifest_path)),
            category=str(raw.get("category") or "utility"),
            description=str(raw.get("description") or ""),
            order=int(raw.get("order") or 100),
            entry=str(raw.get("entry") or "plugin:Plugin"),
            standalone=bool(raw.get("standalone", True)),
            tags=list(raw.get("tags") or []),
            policy_name=str(raw.get("policy_name") or ""),
            department=int(raw.get("department") or 0),
        )
        if not meta.plugin_id:
            raise ValueError("plugin.yaml 缺少 id")
        module_file, class_name = self._resolve_entry(manifest_path.parent, meta.entry)
        module = self._import_module(meta.plugin_id, module_file)
        cls = getattr(module, class_name)
        plugin = cls(meta=meta, context=self.context)
        if not isinstance(plugin, GuiPlugin):
            raise TypeError(f"{class_name} 必须继承 GuiPlugin")
        return plugin

    def _resolve_entry(self, plugin_dir: Path, entry: str) -> Tuple[Path, str]:
        # entry 格式: plugin:ClassName 或 widget:ClassName
        if ":" not in entry:
            return plugin_dir / "plugin.py", entry
        module_key, class_name = entry.split(":", 1)
        return plugin_dir / f"{module_key}.py", class_name

    def _import_module(self, plugin_id: str, module_file: Path) -> Any:
        module_name = f"cu_concrete_gui_plugin_{plugin_id.replace('.', '_')}"
        spec = importlib.util.spec_from_file_location(module_name, str(module_file))
        if spec is None or spec.loader is None:
            raise ImportError(f"无法加载 {module_file}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


def meta_fallback_name(manifest_path: Path) -> str:
    return manifest_path.parent.name
