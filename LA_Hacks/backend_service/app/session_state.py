from __future__ import annotations

from collections import defaultdict, deque
from copy import deepcopy
from threading import Lock
from typing import Deque


class SessionSmootherStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._store: dict[str, Deque[dict[str, float]]] = defaultdict(deque)

    def append(
        self,
        session_id: str,
        probabilities: dict[str, float],
        smoothing_window: int,
    ) -> list[dict[str, float]]:
        with self._lock:
            queue = self._store[session_id]
            queue.append(probabilities)
            while len(queue) > smoothing_window:
                queue.popleft()
            return list(queue)

    def clear(self, session_id: str) -> None:
        with self._lock:
            self._store.pop(session_id, None)

    def clear_all(self) -> int:
        with self._lock:
            count = len(self._store)
            self._store.clear()
            return count


session_smoother_store = SessionSmootherStore()


class SessionScalarStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._store: dict[str, Deque[float]] = defaultdict(deque)

    def append(self, session_id: str, value: float, window: int) -> list[float]:
        with self._lock:
            queue = self._store[session_id]
            queue.append(value)
            while len(queue) > window:
                queue.popleft()
            return list(queue)

    def clear(self, session_id: str) -> None:
        with self._lock:
            self._store.pop(session_id, None)

    def clear_all(self) -> int:
        with self._lock:
            count = len(self._store)
            self._store.clear()
            return count


als_scalar_store = SessionScalarStore()


class EventStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._events_by_user: dict[str, list[dict[str, object]]] = defaultdict(list)

    def append_events(self, user_id: str, events: list[dict[str, object]]) -> int:
        with self._lock:
            user_events = self._events_by_user[user_id]
            user_events.extend(deepcopy(events))
            return len(user_events)

    def get_events(self, user_id: str) -> list[dict[str, object]]:
        with self._lock:
            return deepcopy(self._events_by_user.get(user_id, []))

    def get_latest_event(self, user_id: str) -> dict[str, object] | None:
        with self._lock:
            events = self._events_by_user.get(user_id)
            if not events:
                return None
            return deepcopy(events[-1])

    def clear(self) -> None:
        with self._lock:
            self._events_by_user.clear()

    def total_events(self) -> int:
        with self._lock:
            return sum(len(events) for events in self._events_by_user.values())


watch_event_store = EventStore()


class EdgePacketStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._packets: list[dict[str, object]] = []
        self._version = 0

    def append_packets(self, packets: list[dict[str, object]]) -> int:
        with self._lock:
            self._packets.extend(deepcopy(packets))
            self._version += 1
            return len(self._packets)

    def get_packets(self) -> list[dict[str, object]]:
        with self._lock:
            return deepcopy(self._packets)

    def get_version(self) -> int:
        with self._lock:
            return self._version

    def clear(self) -> None:
        with self._lock:
            self._packets.clear()
            self._version = 0

    def total_packets(self) -> int:
        with self._lock:
            return len(self._packets)


edge_packet_store = EdgePacketStore()
