# Local D&D Adventure Agent

This repository is migrating a small command-line prototype into a local-only Streamlit dungeon master powered by a locally hosted language model, LangChain tools, LangGraph workflows, and lazily loaded Chroma collections. See [Plan.md](Plan.md) for the implementation roadmap and [architecture.drawio](architecture.drawio) for the component diagram.

## Project status

Phases 1 and 2 are implemented: the foundation, local LangChain chat adapter, source-aware SRD ingestion, and lazy edition-scoped Chroma retrieval are in place. Agent workflows, memory, adventure persistence, and the full Streamlit adventure flow remain planned. The console prototype in `Python/` is retained as legacy reference code; its retrieval helper now uses the same Chroma collections.

## Planned behavior

- The player chooses a D&D edition and supplies the world details, starting characters, and optional adventure direction through the UI.
- The agent generates and runs the adventure; it does not invent the player's world or character details without player input.
- The player can choose ReAct or Plan-Execute-Revise and can save, pause, and resume adventures.
- Edition-specific Chroma rule collections are loaded on demand. Campaign content and semantic, local, and episodic memories remain scoped to the user and adventure.
- A local model is configured by path or local endpoint and is never committed to this repository.
- The local-only app has no authentication layer.
- Chat uses an OpenAI-compatible local endpoint configured with `DND_MODEL_BASE_URL` and `DND_MODEL_NAME`; it reports a clear error if the endpoint is unavailable.
- The configured 5e SRD JSON corpus can be indexed into local Chroma by rules domain. Retrieval requires an edition and domain and always filters results by that edition.

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

## Local model and SRD retrieval

The app connects to an OpenAI-compatible local model server (for example, a local inference server exposing `/v1/models`). It does not load model weights in-process. Set `DND_MODEL_BASE_URL`, `DND_MODEL_NAME`, and optionally `DND_MODEL_PATH` in `.env` or the launch environment. `DND_MODEL_PATH` documents where the server's model lives; model files are not read or committed by this app.

The first use of the embedding model may download it to the local Hugging Face cache. To build the configured SRD collections, run:

```powershell
python -m dnd_agent.ingest --edition 5e_srd
```

You can ingest one domain with `--domain rules`, `creatures`, `spells`, or `items`. Chroma data is written under `DND_CHROMA_DIR` (by default `runtime/chroma/`). Each source chunk records edition, domain, source file, source record, and title metadata. Collections are opened only when explicitly ingested or searched. Other editions require explicitly supplied and configured source data; no additional rules corpus is assumed.
