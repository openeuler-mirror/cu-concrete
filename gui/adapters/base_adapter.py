
# -*- coding: utf-8 -*-
"""策略适配契约。"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol


@dataclass
class ActionResult:
    ok: bool
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyInfo:
    name: str
    department: int
    description: str = ""
    module_path: str = ""
    policy_id: str = ""


class IPolicyAdapter(Protocol):
    def list_items(self) -> List[PolicyInfo]:
        ...

    def get_meta(self, name: str) -> Optional[PolicyInfo]:
        ...

    def check(self, name: str) -> ActionResult:
        ...

    def harden(self, name: str) -> ActionResult:
        ...

    def restore(self, name: str) -> ActionResult:
        ...

    def repair(self, name: str) -> ActionResult:
        ...
