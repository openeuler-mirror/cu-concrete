
# -*- coding: utf-8 -*-
"""部门级策略发现。"""
from __future__ import annotations
from pathlib import Path
from typing import Dict, List
from .base_adapter import PolicyInfo
from .policy_adapter import PolicyAdapter


class DepartmentAdapter:
    def __init__(self, repo_root: Path) -> None:
        self.policy_adapter = PolicyAdapter(repo_root)

    def list_departments(self) -> List[int]:
        return [1, 2]

    def list_by_department(self, department: int) -> List[PolicyInfo]:
        return [i for i in self.policy_adapter.list_items() if i.department == department]

    def as_grouped_dict(self) -> Dict[int, List[PolicyInfo]]:
        grouped: Dict[int, List[PolicyInfo]] = {}
        for item in self.policy_adapter.list_items():
            grouped.setdefault(item.department, []).append(item)
        return grouped
