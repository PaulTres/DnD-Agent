# Local D&D Adventure Agent

This repository currently contains a small command-line prototype. The planned replacement is a local-only Streamlit dungeon master powered by a locally hosted language model, LangChain tools, LangGraph workflows, and lazily loaded Chroma collections. See [Plan.md](Plan.md) for the implementation roadmap and [architecture.drawio](architecture.drawio) for the component diagram.

## Project status

Planning and configuration scaffolding only. The application has not yet been migrated to Streamlit or LangGraph. The current prototype lives in `Python/`; it uses a console loop, a FAISS index, and a local `llama-cpp` model path.

## Planned behavior

- The player chooses a D&D edition and supplies the world details, starting characters, and optional adventure direction through the UI.
- The agent generates and runs the adventure; it does not invent the player's world or character details without player input.
- The player can choose ReAct or Plan-Execute-Revise and can save, pause, and resume adventures.
- Edition-specific Chroma rule collections are loaded on demand. Campaign content and semantic, local, and episodic memories remain scoped to the user and adventure.
- A local model is configured by path or local endpoint and is never committed to this repository.
- The local-only app has no authentication layer.

## Configuration

[`config.py`](config.py) is the central source of truth for supported editions, dice, collection naming, and local runtime defaults. Keep generated databases and model weights outside version control.

## Current prototype

The existing scripts are in `Python/` and the current 5e SRD JSON source data is in `Data/`. They are reference material for the migration; they do not yet implement the planned architecture.

## Start using the future app

The Streamlit entry point and dependency setup will be added in a later implementation phase. Follow [Plan.md](Plan.md) for the planned sequence; this README does not claim the new application is runnable yet.
