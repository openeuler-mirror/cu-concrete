# -*- coding: utf-8 -*-
"""插件入口: utility.import_export"""
from __future__ import annotations
import sys
from pathlib import Path

_GUI_ROOT = Path(__file__).resolve().parents[3]
if str(_GUI_ROOT) not in sys.path:
    sys.path.insert(0, str(_GUI_ROOT))

from core.plugin_api import GuiPlugin

import json
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from plugins._shared.gtk_helpers import make_page, make_button_row, make_text_view

class ImportExportPlugin(GuiPlugin):
    def create_widget(self, parent):
        page, body = make_page("导入导出", "导出插件清单与适配器扫描结果；导入 JSON 选中列表")
        self.scroll, self.view = make_text_view("")
        body.pack_start(self.scroll, True, True, 0)
        body.pack_start(make_button_row([
            ("导出插件列表", self._export_plugins),
            ("导出策略列表", self._export_policies),
            ("从剪贴板导入 JSON", self._import_json),
        ]), False, False, 0)
        return page
    def _export_plugins(self, _b):
        # 由宿主 registry 不直接注入时，扫描 manifests
        items = []
        for manifest in sorted((self.context.gui_root / "plugins").rglob("plugin.yaml")):
            items.append(str(manifest.relative_to(self.context.gui_root)))
        text = json.dumps(items, ensure_ascii=False, indent=2)
        self.view.get_buffer().set_text(text)
        out = self.context.gui_root / "config" / "export_plugins.json"
        out.write_text(text, encoding="utf-8")
        self.context.event_bus.publish("status", message=f"已导出 {out}")
    def _export_policies(self, _b):
        adapter = self.context.extras["policy_adapter"]
        data = [{"name": i.name, "department": i.department, "description": i.description} for i in adapter.list_items()]
        text = json.dumps(data, ensure_ascii=False, indent=2)
        self.view.get_buffer().set_text(text)
        out = self.context.gui_root / "config" / "export_policies.json"
        out.write_text(text, encoding="utf-8")
        self.context.event_bus.publish("status", message=f"已导出 {out}")
    def _import_json(self, _b):
        from gi.repository import Gdk
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        text = clipboard.wait_for_text() or ""
        try:
            data = json.loads(text)
            self.view.get_buffer().set_text("导入成功:\n" + json.dumps(data, ensure_ascii=False, indent=2))
            self.context.event_bus.publish("result", message="导入 JSON 成功")
        except Exception as exc:
            self.view.get_buffer().set_text(f"导入失败: {exc}\n原始内容:\n{text}")

