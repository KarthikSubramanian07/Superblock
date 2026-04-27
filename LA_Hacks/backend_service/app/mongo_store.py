"""
mongo_store.py
──────────────────────────────────────────────────────────────────────────
MongoDB Atlas persistence layer for Superblock edge telemetry packets.

Writes every ingested privacy-safe packet to MongoDB Atlas so the data
survives server restarts and can be queried historically.
──────────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

logger = logging.getLogger("superblock.mongo")

MONGO_URI = os.getenv("MONGO_URI", "")
DB_NAME = "superblock"
PACKETS_COLLECTION = "edge_packets"
TILES_COLLECTION = "tile_snapshots"
INTERVENTIONS_COLLECTION = "interventions"


class MongoStore:
    """Thin wrapper around PyMongo for Superblock telemetry persistence."""

    def __init__(self, uri: str = MONGO_URI) -> None:
        self._client: MongoClient | None = None
        self._uri = uri
        self._connected = False

    def connect(self) -> bool:
        """Attempt to connect to MongoDB Atlas. Returns True on success."""
        try:
            self._client = MongoClient(
                self._uri,
                serverSelectionTimeoutMS=5000,
                tls=True,
                tlsAllowInvalidCertificates=True,  # Hackathon demo: ignore SSL cert issues
            )
            # Force a connection test
            self._client.admin.command("ping")
            self._connected = True
            logger.info("✅ Connected to MongoDB Atlas")
            return True
        except (ConnectionFailure, OperationFailure) as exc:
            logger.warning("⚠️  MongoDB Atlas connection failed: %s", exc)
            self._connected = False
            return False

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def db(self):
        if self._client is None:
            raise RuntimeError("MongoStore not connected")
        return self._client[DB_NAME]

    # ── Packet persistence ──────────────────────────────────────────────

    def persist_packets(self, packets: list[dict[str, Any]]) -> int:
        """Insert edge packets into MongoDB. Returns count inserted."""
        if not self._connected or not packets:
            return 0
        try:
            enriched = []
            for p in packets:
                doc = {**p, "persisted_at": datetime.now(timezone.utc).isoformat()}
                enriched.append(doc)
            result = self.db[PACKETS_COLLECTION].insert_many(enriched)
            return len(result.inserted_ids)
        except Exception as exc:
            logger.warning("MongoDB insert_many failed: %s", exc)
            return 0

    def get_packet_count(self) -> int:
        """Return total number of stored packets."""
        if not self._connected:
            return 0
        try:
            return self.db[PACKETS_COLLECTION].count_documents({})
        except Exception:
            return 0

    def get_recent_packets(self, limit: int = 100) -> list[dict[str, Any]]:
        """Return the most recent packets from MongoDB."""
        if not self._connected:
            return []
        try:
            cursor = (
                self.db[PACKETS_COLLECTION]
                .find({}, {"_id": 0})
                .sort("persisted_at", -1)
                .limit(limit)
            )
            return list(cursor)
        except Exception:
            return []

    def get_all_packets(self) -> list[dict[str, Any]]:
        """Return all persisted packets from MongoDB (used to seed in-memory store on startup)."""
        if not self._connected:
            return []
        try:
            return list(self.db[PACKETS_COLLECTION].find({}, {"_id": 0}))
        except Exception:
            return []

    # ── Tile snapshot persistence ────────────────────────────────────────

    def persist_tile_snapshot(self, tiles: list[dict[str, Any]]) -> int:
        """Persist a snapshot of aggregated tile data."""
        if not self._connected or not tiles:
            return 0
        try:
            snapshot = {
                "snapshot_at": datetime.now(timezone.utc).isoformat(),
                "tile_count": len(tiles),
                "tiles": tiles,
            }
            self.db[TILES_COLLECTION].insert_one(snapshot)
            return len(tiles)
        except Exception as exc:
            logger.warning("MongoDB tile snapshot failed: %s", exc)
            return 0

    # ── Intervention persistence ────────────────────────────────────────

    def persist_intervention(self, intervention: dict[str, Any]) -> bool:
        """Persist an agent orchestration / intervention result."""
        if not self._connected:
            return False
        try:
            doc = {
                **intervention,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            self.db[INTERVENTIONS_COLLECTION].insert_one(doc)
            return True
        except Exception as exc:
            logger.warning("MongoDB intervention persist failed: %s", exc)
            return False

    def get_stats(self) -> dict[str, Any]:
        """Return high-level stats about MongoDB collections."""
        if not self._connected:
            return {"connected": False}
        try:
            return {
                "connected": True,
                "database": DB_NAME,
                "total_packets": self.db[PACKETS_COLLECTION].count_documents({}),
                "total_tile_snapshots": self.db[TILES_COLLECTION].count_documents({}),
                "total_interventions": self.db[INTERVENTIONS_COLLECTION].count_documents({}),
            }
        except Exception as exc:
            return {"connected": True, "error": str(exc)}


# Module-level singleton
_store: MongoStore | None = None


def get_mongo_store() -> MongoStore:
    """Return the singleton MongoStore instance, connecting on first call."""
    global _store
    if _store is None:
        _store = MongoStore()
        _store.connect()
    return _store
