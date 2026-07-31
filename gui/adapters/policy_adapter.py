
# -*- coding: utf-8 -*-
"""单个/批量策略适配器：转调现有 department_*_policy 类。"""
from __future__ import annotations
import importlib.util
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from .base_adapter import ActionResult, PolicyInfo

logger = logging.getLogger(__name__)


class PolicyAdapter:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = Path(repo_root)
        self._instance_cache: Dict[str, Any] = {}

    def list_items(self) -> List[PolicyInfo]:
        items: List[PolicyInfo] = []
        for dept in (1, 2):
            items.extend(self._scan_department(dept))
        return items

    def get_meta(self, name: str) -> Optional[PolicyInfo]:
        for info in self.list_items():
            if info.name == name:
                return info
        return None

    def check(self, name: str) -> ActionResult:
        return self._call(name, "check")

    def harden(self, name: str) -> ActionResult:
        return self._call(name, "fix")

    def restore(self, name: str) -> ActionResult:
        return self._call(name, "rollback")

    def repair(self, name: str) -> ActionResult:
        return self._call(name, "reset")

    def _scan_department(self, department: int) -> List[PolicyInfo]:
        folder = self.repo_root / f"department_{department}_policy"
        if not folder.is_dir():
            return []
        result: List[PolicyInfo] = []
        for child in sorted(folder.iterdir()):
            if not child.is_dir() or child.name.startswith("base_") or child.name.startswith("."):
                continue
            py_file = child / f"{child.name}.py"
            if not py_file.exists():
                continue
            description = child.name
            yaml_file = child / f"{child.name}.yaml"
            if yaml_file.exists():
                try:
                    import yaml
                    with open(yaml_file, "r", encoding="utf-8") as handle:
                        cfg = yaml.safe_load(handle) or {}
                    description = str(cfg.get("description") or child.name)
                except Exception:  # noqa: BLE001
                    pass
            result.append(
                PolicyInfo(
                    name=child.name,
                    department=department,
                    description=description,
                    module_path=str(py_file),
                    policy_id=child.name,
                )
            )
        return result

    def _load_instance(self, name: str) -> Any:
        if name in self._instance_cache:
            return self._instance_cache[name]
        info = self.get_meta(name)
        if info is None:
            raise FileNotFoundError(f"未找到策略: {name}")
        module_path = Path(info.module_path)
        policy_dir = module_path.parent
        parent_policy = policy_dir.parent
        for path in (str(self.repo_root), str(parent_policy), str(policy_dir)):
            if path not in sys.path:
                sys.path.insert(0, path)
        spec = importlib.util.spec_from_file_location(name, str(module_path))
        if spec is None or spec.loader is None:
            raise ImportError(f"无法加载 {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cls = getattr(module, name)
        instance = cls()
        self._instance_cache[name] = instance
        return instance

    def _call(self, name: str, method_name: str) -> ActionResult:
        try:
            instance = self._load_instance(name)
            method = getattr(instance, method_name)
            outcome = method()
            if method_name == "check":
                passed = bool(outcome)
                return ActionResult(
                    ok=True,
                    message="已满足加固条件" if passed else "未满足加固条件",
                    data={"passed": passed, "raw": outcome},
                )
            return ActionResult(ok=True, message=f"{method_name} 执行完成", data={"raw": outcome})
        except Exception as exc:  # noqa: BLE001
            logger.exception("策略调用失败 %s.%s", name, method_name)
            return ActionResult(ok=False, message=str(exc), data={"error": str(exc)})
