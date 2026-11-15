"""Command line entry point for explicit local SRD ingestion."""

from __future__ import annotations

import argparse

from config import EDITIONS
from dnd_agent.retrieval import EditionKnowledgeBase


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest configured SRD JSON into Chroma.")
    parser.add_argument("--edition", choices=tuple(EDITIONS), default="5e_srd")
    parser.add_argument("--domain", help="Ingest one domain; default is every domain.")
    args = parser.parse_args()
    knowledge = EditionKnowledgeBase()
    summaries = (
        [knowledge.ingest_domain(args.edition, args.domain)]
        if args.domain
        else knowledge.ingest_edition(args.edition)
    )
    for summary in summaries:
        print(f"{summary.edition}/{summary.domain}: {summary.documents} chunks -> "
              f"{summary.collection}")


if __name__ == "__main__":
    main()
