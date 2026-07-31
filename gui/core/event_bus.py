# -*- coding: utf-8 -*-
"""轻量事件总线：progress / result / log / status。"""
from __future__ import annotations
from collections import defaultdict
from typing import Any, Callable, DefaultDict, List


class EventBus:
    def __init__(self) -> None:
        self._subscribers: DefaultDict[str, List[Callable[..., None]]] = defaultdict(list)

    def subscribe(self, event_name: str, callback: Callable[..., None]) -> None:
        self._subscribers[event_name].append(callback)

    def unsubscribe(self, event_name: str, callback: Callable[..., None]) -> None:
        if callback in self._subscribers[event_name]:
            self._subscribers[event_name].remove(callback)

    def publish(self, event_name: str, **payload: Any) -> None:
        for callback in list(self._subscribers.get(event_name, [])):
            try:
                callback(**payload)
            except Exception as exc:  # noqa: BLE001
                print(f"[EventBus] handler error on {event_name}: {exc}")
