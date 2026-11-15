"""Central configuration and shared registries for the planned local D&D app.

This file intentionally contains configuration only. Application services and the
Streamlit/LangGraph runtime are future implementation work tracked in Plan.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent


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
    """Edition metadata and source locations used by ingestion and UI."""

    key: str
    label: str
    source_path: Path | None = None
    supported: bool = False

    @property
    def collection_names(self) -> dict[str, str]:
        """Stable names for edition-specific rules collections."""
        return {
            domain: f"rules_{self.key}_{domain}"
            for domain in RULE_DOMAINS
        }


# Canonical registry. Add an edition only when its source material is available.
EDITIONS: dict[str, EditionConfig] = {
    "5e_srd": EditionConfig(
        key="5e_srd",
        label="D&D 5e (SRD)",
        source_path=PROJECT_ROOT / "Data",
        supported=True,
    ),
    "dnd_2024": EditionConfig(
        key="dnd_2024",
        label="D&D 2024",
        supported=False,
    ),
}

RULE_DOMAINS: tuple[str, ...] = ("rules", "creatures", "spells", "items")

# All standard D&D polyhedral dice plus percentile die. Used by UI and dice tool.
DICE_SIDES: tuple[int, ...] = (4, 6, 8, 10, 12, 20, 100)
DICE_LABELS: dict[int, str] = {sides: f"d{sides}" for sides in DICE_SIDES}

# Shared user/adventure memory collections; filter every operation by metadata.
MEMORY_COLLECTIONS: dict[MemoryKind, str] = {
    MemoryKind.SEMANTIC: "user_semantic_memory",
    MemoryKind.EPISODIC: "adventure_episodes",
}
MEMORY_FILTER_KEYS: tuple[str, ...] = ("user_id", "adventure_id")

# Local runtime defaults. Override through environment/local config in the app.
DEFAULT_WORKFLOW = Workflow.REACT
CHROMA_PERSIST_DIR = PROJECT_ROOT / "runtime" / "chroma"
CHECKPOINT_DIR = PROJECT_ROOT / "runtime" / "checkpoints"
ADVENTURE_DATA_DIR = PROJECT_ROOT / "runtime" / "adventures"
LOCAL_MODEL_BASE_URL = "http://127.0.0.1:1234/v1"
LOCAL_MODEL_NAME = "local-model"
LOCAL_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
MAX_AGENT_STEPS = 12
MAX_PLAN_REVISIONS = 3
MAX_DICE_COUNT = 100
MAX_DICE_MODIFIER = 1000

