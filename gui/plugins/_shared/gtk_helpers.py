# -*- coding: utf-8 -*-
"""GTK 小组件工厂。"""
from __future__ import annotations
from typing import Callable, Iterable, Tuple
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


def make_page(title: str, subtitle: str = "") -> Tuple[Gtk.Box, Gtk.Box]:
    page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    page.set_margin_top(12)
    page.set_margin_bottom(12)
    page.set_margin_start(12)
    page.set_margin_end(12)
    label = Gtk.Label()
    label.set_markup(f"<span size='large'><b>{title}</b></span>")
    label.set_xalign(0)
    page.pack_start(label, False, False, 0)
    if subtitle:
        sub = Gtk.Label(label=subtitle)
        sub.set_xalign(0)
        sub.set_line_wrap(True)
        page.pack_start(sub, False, False, 0)
    body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    page.pack_start(body, True, True, 0)
    return page, body


def make_button_row(actions: Iterable[Tuple[str, Callable]]) -> Gtk.Box:
    row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    for text, callback in actions:
        button = Gtk.Button(label=text)
        button.connect("clicked", callback)
        row.pack_start(button, False, False, 0)
    return row


def make_text_view(text: str = "") -> Tuple[Gtk.ScrolledWindow, Gtk.TextView]:
    view = Gtk.TextView()
    view.set_editable(False)
    view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
    view.get_buffer().set_text(text)
    scroll = Gtk.ScrolledWindow()
    scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    scroll.add(view)
    scroll.set_vexpand(True)
    return scroll, view


def append_text(view: Gtk.TextView, text: str) -> None:
    buffer = view.get_buffer()
    end = buffer.get_end_iter()
    if not text.endswith("\n"):
        text = text + "\n"
    buffer.insert(end, text)
