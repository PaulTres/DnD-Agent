"""Streamlit entry point for the local D&D adventure agent."""

from __future__ import annotations

import streamlit as st

from config import EDITIONS, Workflow, get_settings
from dnd_agent.storage import StorageLayout, get_or_create_user_id


def main() -> None:
    st.set_page_config(page_title="D&D Adventure Agent", page_icon="🎲", layout="centered")
    st.title("D&D Adventure Agent")
    st.caption("Local adventure workspace · foundation phase")

    settings = get_settings()
    layout = StorageLayout.from_settings(settings)
    layout.create_base_directories()
    get_or_create_user_id(layout.profile_dir)

    st.info(
        "The app foundation is ready. Adventure generation, retrieval, and save/resume "
        "flows are being added in later implementation phases."
    )

    st.subheader("Adventure setup")
    edition_labels = {key: edition.label for key, edition in EDITIONS.items()}
    st.selectbox("Rules edition", options=list(edition_labels), format_func=edition_labels.get)
    st.selectbox(
        "Agent workflow",
        options=list(Workflow),
        format_func=lambda workflow: {
            Workflow.REACT: "ReAct",
            Workflow.PLAN_EXECUTE_REVISE: "Plan · Execute · Revise",
        }[workflow],
    )
    st.text_area("World details", placeholder="Describe the setting you want to play in.")
    st.text_area("Starting characters", placeholder="Describe the player characters.")
    st.text_area("Optional adventure pointers", placeholder="Themes, goals, or opening ideas.")
    st.caption("Adventure creation will be available after the agent workflow phase.")

    with st.expander("Local configuration"):
        st.write(f"Model endpoint: `{settings.model_base_url}`")
        st.write(f"Model name: `{settings.model_name}`")
        if settings.model_path is not None:
            st.write(f"Model path: `{settings.model_path}`")
        st.write(f"Embedding model: `{settings.embedding_model}`")
        st.write(f"Adventure data directory: `{layout.adventures_dir}`")


if __name__ == "__main__":
    main()
