"""State persistence / checkpointing for the ECOS simulation.

This module provides a minimal, dependency-free JSON checkpoint
mechanism. The read path is intentionally **fail-soft**: a missing or
corrupt checkpoint never raises, so the caller can decide to start
fresh. The write path is **atomic** (temp file + ``os.replace``) so a
crash mid-write cannot leave a half-written checkpoint behind.

Combined with the fail-closed ``restart: on-failure`` container policy
in ``docker-compose.yml``, this gives the long-running simulation a
durable, crash-safe state file instead of silently losing all
in-memory state on restart.
"""

import json
import os
import tempfile
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Default location of the simulation checkpoint (relative to repo root).
DEFAULT_CHECKPOINT_PATH = "output/checkpoint.json"


def _is_json_serializable(value: Any) -> bool:
    """Best-effort check whether ``value`` can round-trip through JSON."""
    try:
        json.dumps(value)
        return True
    except (TypeError, ValueError):
        return False


def _clean_attrs(data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Return a JSON-safe copy of ``data``, coercing or dropping bad values.

    Values that are natively JSON-serializable are kept as-is. Values that
    are not (e.g. ``datetime``, custom objects) are coerced to ``str`` as a
    last resort. If even ``str()`` fails, the key is dropped entirely. This
    guarantees the function never raises.
    """
    cleaned: Dict[str, Any] = {}
    if not data:
        return cleaned
    for key, value in data.items():
        if _is_json_serializable(value):
            cleaned[key] = value
            continue
        try:
            cleaned[key] = str(value)
        except Exception:
            # Truly un-stringable; drop rather than crash.
            continue
    return cleaned


def save_checkpoint(state: dict, path: str) -> None:
    """Atomically JSON-serialize ``state`` to ``path``.

    Writes to a temporary file in the same directory, then uses
    ``os.replace`` to swap it into place. ``os.replace`` is atomic on
    both POSIX and Windows, so readers never observe a partial file.
    """
    if not isinstance(state, dict):
        raise TypeError("save_checkpoint expects a dict state")

    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    tmp_path = None
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=directory or ".", suffix=".ckpt.tmp"
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as fh:
            json.dump(state, fh, indent=2, default=str)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, path)
        tmp_path = None
    finally:
        if tmp_path is not None and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def load_checkpoint(path: str) -> Optional[dict]:
    """Load and parse a checkpoint dict from ``path``.

    Returns the parsed dict on success. Returns ``None`` when the file is
    missing, empty, not valid JSON, or not a JSON object. Never raises on
    the read path — a warning is logged instead so the caller can fall
    back to a fresh start.
    """
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        logger.warning(
            "Checkpoint at %s is missing or corrupt; starting fresh. (%s)",
            path,
            exc,
        )
        return None

    if not isinstance(data, dict):
        logger.warning(
            "Checkpoint at %s is not a JSON object; starting fresh.", path
        )
        return None
    return data


def extract_world_snapshot(world_state: Any) -> Dict[str, Any]:
    """Build a defensive, JSON-serializable snapshot of a WorldStateGraph.

    The returned structure is::

        {
            "current_tick": int,
            "nodes": [{"id": ..., "type": ..., "attrs": {...}}, ...],
            "edges": [{"source": ..., "target": ..., "attrs": {...}}, ...],
        }

    ``current_tick`` is read from ``world_state.current_tick`` (default 0)
    so callers may set it before capturing a checkpoint.

    Non-serializable attributes are coerced to ``str`` (or skipped) rather
    than crashing, making this safe to call on a live, partially-populated
    world. Any unexpected failure returns a minimal empty snapshot.
    """
    snapshot: Dict[str, Any] = {"current_tick": 0, "nodes": [], "edges": []}

    try:
        tick = getattr(world_state, "current_tick", 0)
        snapshot["current_tick"] = int(tick) if tick is not None else 0
    except (TypeError, ValueError):
        snapshot["current_tick"] = 0

    try:
        graph = getattr(world_state, "graph", None)
        if graph is None:
            return snapshot

        # Nodes: separate the "type" tag from the remaining attributes.
        for node_id, data in graph.nodes(data=True):
            try:
                node_type = (data or {}).get("type", "unknown")
                attrs = _clean_attrs(
                    {k: v for k, v in (data or {}).items() if k != "type"}
                )
                snapshot["nodes"].append(
                    {"id": node_id, "type": node_type, "attrs": attrs}
                )
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Skipping node %s: %s", node_id, exc)
                continue

        # Edges: keys are (u, v, key, data); pull the edge type out too.
        for u, v, _key, data in graph.edges(keys=True, data=True):
            try:
                attrs = dict(data or {})
                edge_type = attrs.pop("type", "unknown")
                attrs = _clean_attrs(attrs)
                attrs.setdefault("type", edge_type)
                snapshot["edges"].append(
                    {"source": u, "target": v, "attrs": attrs}
                )
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Skipping edge %s->%s: %s", u, v, exc)
                continue
    except Exception as exc:
        logger.warning("extract_world_snapshot partially failed: %s", exc)

    return snapshot
