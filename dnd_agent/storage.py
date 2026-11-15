"""Foundational local storage layout and identity helpers.

Adventure serialization and checkpoint persistence are implemented in later
phases. These helpers establish stable IDs and the versioned export envelope
those services will use.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from config import (
    ADVENTURE_SCHEMA_VERSION,
    CHECKPOINT_SCHEMA_VERSION,
    EXPORT_FILE_NAMES,
    EXPORT_FORMAT,
    EXPORT_FORMAT_VERSION,
    EXPORT_MANIFEST_FILENAME,
    RuntimeSettings,
    SCHEMA_VERSION,
    get_settings,
)


@dataclass(frozen=True)
class StorageLayout:
    """Resolved paths for local profile, adventure, vector, and checkpoint data."""

    root: Path
    profile_dir: Path
    adventures_dir: Path
    checkpoints_dir: Path
    chroma_dir: Path

    @classmethod
    def from_settings(cls, settings: RuntimeSettings | None = None) -> "StorageLayout":
        settings = settings or get_settings()
        return cls(
            root=settings.adventure_dir.parent,
            profile_dir=settings.profile_dir,
            adventures_dir=settings.adventure_dir,
            checkpoints_dir=settings.checkpoint_dir,
            chroma_dir=settings.chroma_dir,
        )

    def create_base_directories(self) -> None:
        """Create only the local directories needed by the app shell."""
        for directory in (
            self.profile_dir,
            self.adventures_dir,
            self.checkpoints_dir,
            self.chroma_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    def adventure_dir(self, user_id: str, adventure_id: str) -> Path:
        return self.adventures_dir / validate_id(user_id) / validate_id(adventure_id)

    def checkpoint_path(self, user_id: str, adventure_id: str) -> Path:
        return self.checkpoints_dir / validate_id(user_id) / f"{validate_id(adventure_id)}.json"


def new_id() -> str:
    """Return a stable, URL-safe UUID for a user or adventure record."""
    return str(uuid4())


def validate_id(value: str) -> str:
    """Validate a persisted identifier before using it in a local path."""
    try:
        return str(UUID(value))
    except (ValueError, AttributeError, TypeError) as exc:
        raise ValueError("Identifier must be a UUID string.") from exc


def get_or_create_user_id(profile_dir: Path) -> str:
    """Load the persistent local profile ID or create it on first launch."""
    profile_dir.mkdir(parents=True, exist_ok=True)
    profile_path = profile_dir / "profile.json"
    if profile_path.exists():
        try:
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            return validate_id(profile["user_id"])
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise RuntimeError(
                f"Could not read the local profile at {profile_path}: {exc}"
            ) from exc

    user_id = new_id()
    payload = {
        "schema_version": SCHEMA_VERSION,
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    temporary_path = profile_path.with_suffix(".json.tmp")
    temporary_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary_path.replace(profile_path)
    return user_id


def export_manifest(adventure_id: str, user_id: str) -> dict[str, object]:
    """Return the versioned manifest for a ZIP export.

    The archive contains ``manifest.json`` plus the canonical JSON/JSONL
    members in ``EXPORT_FILE_NAMES``. The members hold the adventure record,
    chat, structured campaign state, and graph checkpoint respectively.
    """
    return {
        "format": EXPORT_FORMAT,
        "format_version": EXPORT_FORMAT_VERSION,
        "manifest_file": EXPORT_MANIFEST_FILENAME,
        "schema_version": ADVENTURE_SCHEMA_VERSION,
        "checkpoint_schema_version": CHECKPOINT_SCHEMA_VERSION,
        "user_id": validate_id(user_id),
        "adventure_id": validate_id(adventure_id),
        "files": list(EXPORT_FILE_NAMES),
    }
