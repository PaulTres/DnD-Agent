# Implementation Plan

This file is the working checklist for replacing the prototype with a local, multi-edition D&D adventure agent. Completed boxes represent planning artifacts already prepared; application work remains unchecked. Do not mark a step complete until its deliverable exists and has been reviewed.

Architecture reference: [architecture.drawio](architecture.drawio).

## Decisions and requirements

- [x] Keep the app local-only; authentication is out of scope.
- [x] Use Streamlit for the basic UI.
- [x] Use LangChain for model/tool integration and LangGraph for the agent workflows and persistence/checkpoint flow.
- [x] Support both ReAct and Plan-Execute-Revise workflows, selected per adventure.
- [x] Host the LLM locally. Configure its local path or endpoint; never commit model weights.
- [x] Keep the LLM responsible for generating the adventure. Players provide world details, starting characters, and optional adventure pointers.
- [x] Support multiple D&D editions. Each edition has edition-specific Chroma collections and is loaded lazily on selection/use.
- [x] Include semantic, local, and episodic memory, with user/adventure scoping for chat data.
- [x] Include a monster generator and a dice roller that supports every standard D&D die (d4, d6, d8, d10, d12, d20, d100), plus validated count and modifier inputs. More tools may be added in the future.
- [x] Allow adventures to be saved, paused, listed, and resumed with their edition, workflow, player inputs, conversation, graph checkpoint, and campaign state.
- [x] Keep central defaults and shared registries in `config.py`.

## Phases

### 0. Planning and scaffolding

- [x] Record requirements, architecture decisions, and implementation checklist in `Plan.md`.
- [x] Add Python project instructions in `Agents.md`.
- [x] Add the component diagram in `architecture.drawio` and reference it from the plan, README, and agent instructions.
- [x] Add the shared configuration scaffold in `config.py`.
- [x] Update README to describe current status, target behavior, and the migration plan.
- [x] Keep local model files and generated local vector/checkpoint data out of git.

### 1. Foundation and configuration

- [x] Establish the Python package structure, dependency manifest, and Streamlit entry point.
- [x] Move shared runtime settings and registries to `config.py`; add environment-based overrides for local model endpoint/path, embedding model, Chroma location, checkpoint location, and limits.
- [x] Define typed edition metadata, stable edition identifiers, source-data locations, and collection names. Add no unsupported rule data by assumption.
- [x] Define persistent local storage layout, stable user/adventure identifiers, schema versions, and backup/export format.
- [x] Keep model weights, local credentials if any, vector databases, checkpoints, and user saves out of source control.

### 2. Local model and retrieval

- [ ] Integrate a locally hosted chat model through LangChain using a configurable local provider/endpoint; fail clearly when unavailable.
- [ ] Configure local embeddings and document-loading/chunking with source provenance.
- [ ] Design edition-scoped Chroma collections by rules domain (for example rules, creatures, spells, and items) with stable metadata and provenance. Implement lazy creation/loading and cache collections only when an edition is selected or a tool needs them.
- [ ] Ingest the existing 5e SRD JSON as the initial supported corpus; add other editions only from explicitly supplied/licensed data sources.
- [ ] Ensure retrieval always filters by edition and returns source metadata; do not mix rules across editions.
- [ ] Retire the FAISS index path after equivalent Chroma retrieval is in place.

### 3. Memory and adventure persistence

- [ ] Define semantic memory as durable, searchable campaign/player facts and preferences, stored in a shared semantic-memory collection with `user_id`, `adventure_id` (optional), edition, and provenance metadata.
- [ ] Define local memory as the current authoritative adventure state (characters, location, quests, inventory, NPCs, flags, and unresolved choices) in structured per-adventure storage/state, not as unstructured vector search.
- [ ] Define episodic memory as searchable summaries of completed scenes/turns in a shared episodic collection filtered by `user_id` and `adventure_id`; retain timestamps and links to source turns.
- [ ] Define campaign-input storage for player-provided world details, characters, and optional pointers, preserving them as authoritative source material and associating them with the adventure.
- [ ] Implement LangGraph checkpoint persistence and explicit save/pause/resume/list flows; restore the same edition, workflow, graph state, and adventure identifier.
- [ ] Add local data migration/schema version handling and a user-controlled export/import path for saved adventures.

### 4. Tools and graph workflows

- [ ] Implement a typed dice tool using the canonical dice registry from `config.py`, with validation for all supported die types, roll count, and modifier; keep randomness in the tool, not model-generated text.
- [ ] Implement a monster generation tool that uses the active edition's retrieved creature rules and campaign context, and labels generated content distinctly from sourced rules.
- [ ] Add retrieval, memory read/write, and adventure-state tools with scoped inputs and explicit descriptions for the model.
- [ ] Build a LangGraph ReAct workflow with tool execution, bounded turns, error handling, and safe termination.
- [ ] Build a Plan-Execute-Revise workflow with explicit plan, execution, review/revision, and player-facing response nodes; bound iterations and preserve plan/checkpoint state.
- [ ] Make workflow selection explicit and persist it for the adventure; keep tool outputs and durable state updates structured.
- [ ] Ensure the agent does not claim dice outcomes, rules citations, player character facts, or world details that were not supplied or retrieved.

### 5. Streamlit interface

- [ ] Provide an edition dropdown populated from the supported-edition registry.
- [ ] Provide text input and file upload for world details, starting characters, and optional adventure pointers; show the user what was accepted before starting.
- [ ] Provide workflow selection (ReAct or Plan-Execute-Revise), adventure creation, pause/save, saved-adventure listing, and resume.
- [ ] Provide a chat/adventure view that displays agent narration, tool results, dice rolls, and sourced rules clearly.
- [ ] Keep the UI local-only and avoid authentication work.
- [ ] Make app state safe across Streamlit reruns; do not rely on transient session state as the only copy of a saved adventure.

### 6. Quality, documentation, and release readiness

- [ ] Add tests for configuration, dice validation, tool schemas, edition isolation, lazy collection loading, memory scoping, graph workflows, and save/resume.
- [ ] Add local setup instructions, dependency/model configuration, data ingestion guidance, supported edition/source notes, and troubleshooting to README.
- [ ] Verify no model files, generated Chroma data, private campaign saves, or local checkpoints are tracked.
- [ ] Review the implementation against [architecture.drawio](architecture.drawio) and update the diagram and this plan as architecture changes.

## Acceptance criteria

- A player can choose a supported edition, provide their setting and characters, optionally add adventure pointers, choose either workflow, and start an adventure locally.
- The player can pause/close the app and resume the same adventure with its edition, workflow, conversation, checkpoint, and structured state restored.
- Rules retrieval is edition-isolated and lazy; user memories and episodes are scoped to the right user/adventure.
- Dice results come from the dice tool, and monster generation is available through an agent tool.
- Local model and generated data paths are configurable and excluded from commits.
