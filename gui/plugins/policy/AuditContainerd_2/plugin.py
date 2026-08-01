# -*- coding: utf-8 -*-
"""插件入口: policy.AuditContainerd_2"""
from __future__ import annotations
import sys
from pathlib import Path

_GUI_ROOT = Path(__file__).resolve().parents[3]
if str(_GUI_ROOT) not in sys.path:
    sys.path.insert(0, str(_GUI_ROOT))

from core.plugin_api import GuiPlugin
from plugins._shared.policy_detail_panel import PolicyDetailPanel


class Policy_AuditContainerd_2_Plugin(GuiPlugin):
    POLICY_NAME = "AuditContainerd_2"

    def create_widget(self, parent):
        return PolicyDetailPanel(
            title=self.meta.name,
            subtitle=self.meta.description or self.POLICY_NAME,
            policy_name=self.POLICY_NAME,
            department=int(self.meta.department or 2),
            context=self.context,
        )
