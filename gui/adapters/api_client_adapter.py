
# -*- coding: utf-8 -*-
"""API 侧适配：优先读本地配置/结果，可选 HTTP。"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from .base_adapter import ActionResult


class ApiClientAdapter:
    def __init__(self, repo_root: Path, base_url: str = "http://127.0.0.1:8000") -> None:
        self.repo_root = Path(repo_root)
        self.base_url = base_url.rstrip("/")
        self.api_dir = self.repo_root / "api"

    def list_pools(self) -> ActionResult:
        config_path = self.api_dir / "config.yaml"
        pools: List[Dict[str, Any]] = []
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}
            if isinstance(data, dict):
                raw = data.get("pools") or data.get("cloud_pools") or data
                if isinstance(raw, list):
                    pools = raw
                elif isinstance(raw, dict):
                    pools = [{"id": k, "name": v} for k, v in raw.items()]
            elif isinstance(data, list):
                pools = data
        return ActionResult(ok=True, message=f"共 {len(pools)} 个云池", data={"list": pools})

    def list_results(self) -> ActionResult:
        result_dir = self.repo_root / "data" / "results"
        files: List[str] = []
        if result_dir.is_dir():
            files = sorted(str(p.name) for p in result_dir.iterdir() if p.is_file())
        return ActionResult(ok=True, message=f"共 {len(files)} 个结果文件", data={"list": files})

    def read_conf_data(self) -> ActionResult:
        path = self.api_dir / "conf_data.json"
        if not path.exists():
            return ActionResult(ok=False, message="conf_data.json 不存在")
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return ActionResult(ok=True, message="已读取 conf_data.json", data={"content": data})

    def read_conf_harden(self) -> ActionResult:
        path = self.api_dir / "conf_harden.json"
        if not path.exists():
            return ActionResult(ok=False, message="conf_harden.json 不存在")
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return ActionResult(ok=True, message="已读取 conf_harden.json", data={"content": data})
