# Local D&D Adventure Agent

This repository is migrating a small command-line prototype into a local-only Streamlit dungeon master powered by a locally hosted language model, LangChain tools, LangGraph workflows, and lazily loaded Chroma collections. See [Plan.md](Plan.md) for the implementation roadmap and [architecture.drawio](architecture.drawio) for the component diagram.

## Project status

Phase 1 foundation is implemented: the `dnd_agent` Python package, dependency manifest, environment-driven configuration, local storage conventions, and Streamlit entry point are in place. Adventure generation, retrieval, LangGraph workflows, and save/resume are not implemented yet. The legacy prototype remains in `Python/`; it uses a console loop and FAISS.

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

## Local setup

Use Python 3.11 or newer. From the repository root, install the project and start the Streamlit foundation:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
streamlit run app.py
```

Copy `.env.example` to `.env` and adjust the `DND_*` variables as needed. The app reads environment variables directly; load `.env` in your shell or IDE before launch. Local generated data defaults to the ignored `runtime/` directory and can be relocated with `DND_DATA_DIR` or the individual path overrides. Model weights and local data are not included in the project. The current UI is a setup shell; adventure actions become available in later phases.
