"""Shared configuration and registries for the local D&D adventure app.

Environment variables are read when :func:`get_settings` is called, so tests,
Streamlit reruns, and command line entry points can all use the same defaults.
Relative paths are resolved from the repository root; absolute paths are kept.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Mapping


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "Data"
RULE_DOMAINS: tuple[str, ...] = ("rules", "creatures", "spells", "items")


class Workflow(str, Enum):
    """Supported agent control flows."""

    REACT = "react"
    PLAN_EXECUTE_REVISE = "plan_execute_revise"


class MemoryKind(str, Enum):
    """Memory categories used by the planned agent."""

    SEMANTIC = "semantic"
    LOCAL = "local"
    EPISODIC = "episodic"


@dataclass(frozen=True)
class EditionConfig:
    """Stable edition identity and locations for source data and collections."""

    key: str
    label: str
    source_path: Path
    collections: Mapping[str, str]
    source_files: Mapping[str, tuple[str, ...]]
    source_name: str


def _edition(
    key: str,
    label: str,
    source_path: Path,
    source_name: str,
    source_files: Mapping[str, tuple[str, ...]],
) -> EditionConfig:
    return EditionConfig(
        key=key,
        label=label,
        source_path=source_path,
        collections=MappingProxyType(
            {domain: f"rules_{key}_{domain}" for domain in RULE_DOMAINS}
        ),
        source_files=MappingProxyType(dict(source_files)),
        source_name=source_name,
    )


# Only editions with an identified source corpus belong in this supported registry.
EDITIONS: Mapping[str, EditionConfig] = MappingProxyType(
    {
        "5e_srd": _edition(
            key="5e_srd",
            label="D&D 5e (SRD)",
            source_path=DATA_DIR,
            source_name="Repository 5e SRD JSON corpus",
            source_files={
                "rules": (
                    "5e-SRD-Ability-Scores.json", "5e-SRD-Alignments.json",
                    "5e-SRD-Backgrounds.json", "5e-SRD-Classes.json",
                    "5e-SRD-Conditions.json", "5e-SRD-Damage-Types.json",
                    "5e-SRD-Features.json", "5e-SRD-Feats.json",
                    "5e-SRD-Languages.json", "5e-SRD-Levels.json",
                    "5e-SRD-Magic-Schools.json", "5e-SRD-Proficiencies.json",
                    "5e-SRD-Races.json", "5e-SRD-Rule-Sections.json",
                    "5e-SRD-Rules.json", "5e-SRD-Skills.json",
                    "5e-SRD-Subclasses.json", "5e-SRD-Subraces.json",
                    "5e-SRD-Traits.json",
                ),
                "creatures": ("5e-SRD-Monsters.json",),
                "spells": ("5e-SRD-Spells.json",),
                "items": (
                    "5e-SRD-Equipment.json", "5e-SRD-Equipment-Categories.json",
                    "5e-SRD-Magic-Items.json", "5e-SRD-Weapon-Properties.json",
                ),
            },
        ),
    }
)

# Canonical registry for the standard D&D polyhedral dice and percentile die.
DICE_SIDES: tuple[int, ...] = (4, 6, 8, 10, 12, 20, 100)
DICE_LABELS: Mapping[int, str] = MappingProxyType(
    {sides: f"d{sides}" for sides in DICE_SIDES}
)

MEMORY_COLLECTIONS: Mapping[MemoryKind, str] = MappingProxyType(
    {
        MemoryKind.SEMANTIC: "user_semantic_memory",
        MemoryKind.EPISODIC: "adventure_episodes",
    }
)
MEMORY_FILTER_KEYS: tuple[str, ...] = ("user_id", "adventure_id")

DEFAULT_WORKFLOW = Workflow.REACT
SCHEMA_VERSION = 1
ADVENTURE_SCHEMA_VERSION = SCHEMA_VERSION
CHECKPOINT_SCHEMA_VERSION = SCHEMA_VERSION
EXPORT_FORMAT = "dnd-adventure-export"
EXPORT_FORMAT_VERSION = 1
EXPORT_MANIFEST_FILENAME = "manifest.json"
EXPORT_FILE_NAMES: tuple[str, ...] = (
    "adventure.json",
    "chat.jsonl",
    "campaign_state.json",
    "checkpoint.json",
)

# Conventional application data layout. Override individual locations using the
# environment variables represented in RuntimeSettings below.
DEFAULT_DATA_ROOT = PROJECT_ROOT / "runtime"
DEFAULT_CHROMA_DIR = DEFAULT_DATA_ROOT / "chroma"
DEFAULT_CHECKPOINT_DIR = DEFAULT_DATA_ROOT / "checkpoints"
DEFAULT_ADVENTURE_DIR = DEFAULT_DATA_ROOT / "adventures"
DEFAULT_PROFILE_DIR = DEFAULT_DATA_ROOT / "profile"
LOCAL_MODEL_BASE_URL = "http://127.0.0.1:1234/v1"
LOCAL_MODEL_NAME = "local-model"
LOCAL_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
MAX_AGENT_STEPS = 12
MAX_PLAN_REVISIONS = 3
MAX_DICE_COUNT = 100
MAX_DICE_MODIFIER = 1000


@dataclass(frozen=True)
class RuntimeSettings:
    """Resolved local runtime settings; values may come from environment."""

    model_base_url: str
    model_name: str
    model_path: Path | None
    embedding_model: str
    chroma_dir: Path
    checkpoint_dir: Path
    adventure_dir: Path
    profile_dir: Path
    max_agent_steps: int
    max_plan_revisions: int
    max_dice_count: int
    max_dice_modifier: int


def _path_setting(name: str, default: Path, root: Path) -> Path:
    raw = os.getenv(name)
    if not raw:
        return default
    path = Path(raw).expanduser()
    return path if path.is_absolute() else root / path


def _optional_path_setting(name: str) -> Path | None:
    raw = os.getenv(name, "").strip()
    if not raw:
        return None
    path = Path(raw).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def _positive_int_setting(name: str, default: int, *, allow_zero: bool = False) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}.") from exc
    minimum = 0 if allow_zero else 1
    if value < minimum:
        qualifier = "zero or greater" if allow_zero else "greater than zero"
        raise ValueError(f"{name} must be {qualifier}, got {value}.")
    return value


def _string_setting(name: str, default: str) -> str:
    value = os.getenv(name, default).strip()
    if not value:
        raise ValueError(f"{name} must not be empty.")
    return value


def get_settings() -> RuntimeSettings:
    """Build validated settings from environment overrides and shared defaults.

    Supported variables: ``DND_DATA_DIR``, ``DND_MODEL_BASE_URL``,
    ``DND_MODEL_NAME``, ``DND_MODEL_PATH``, ``DND_EMBEDDING_MODEL``,
    ``DND_CHROMA_DIR``, ``DND_CHECKPOINT_DIR``, ``DND_ADVENTURE_DIR``,
    ``DND_PROFILE_DIR``, and ``DND_MAX_*`` limits.
    """

    data_root = _path_setting("DND_DATA_DIR", DEFAULT_DATA_ROOT, PROJECT_ROOT)
    return RuntimeSettings(
        model_base_url=_string_setting("DND_MODEL_BASE_URL", LOCAL_MODEL_BASE_URL),
        model_name=_string_setting("DND_MODEL_NAME", LOCAL_MODEL_NAME),
        model_path=_optional_path_setting("DND_MODEL_PATH"),
        embedding_model=_string_setting("DND_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL),
        chroma_dir=_path_setting("DND_CHROMA_DIR", data_root / "chroma", PROJECT_ROOT),
        checkpoint_dir=_path_setting(
            "DND_CHECKPOINT_DIR", data_root / "checkpoints", PROJECT_ROOT
        ),
        adventure_dir=_path_setting(
            "DND_ADVENTURE_DIR", data_root / "adventures", PROJECT_ROOT
        ),
        profile_dir=_path_setting("DND_PROFILE_DIR", data_root / "profile", PROJECT_ROOT),
        max_agent_steps=_positive_int_setting("DND_MAX_AGENT_STEPS", MAX_AGENT_STEPS),
        max_plan_revisions=_positive_int_setting(
            "DND_MAX_PLAN_REVISIONS", MAX_PLAN_REVISIONS, allow_zero=True
        ),
        max_dice_count=_positive_int_setting("DND_MAX_DICE_COUNT", MAX_DICE_COUNT),
        max_dice_modifier=_positive_int_setting(
            "DND_MAX_DICE_MODIFIER", MAX_DICE_MODIFIER, allow_zero=True
        ),
    )


# Backwards-compatible default constants for callers that need paths at import time.
CHROMA_PERSIST_DIR = DEFAULT_CHROMA_DIR
CHECKPOINT_DIR = DEFAULT_CHECKPOINT_DIR
ADVENTURE_DATA_DIR = DEFAULT_ADVENTURE_DIR
