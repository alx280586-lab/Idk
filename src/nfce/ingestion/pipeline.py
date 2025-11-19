"""End-to-end Wikipedia ingestion pipeline."""
from __future__ import annotations

from typing import Iterable
from pathlib import Path
from ..config import IngestionConfig
from .wikipedia_dump_parser import stream_articles
from .section_to_meaning import summarize_sections
from .infobox_extractor import extract_infobox
from .link_and_category_graph_builder import parse_links, parse_categories
from .node_factory import create_node
from ..knowledge_graph.graph import InMemoryGraph


def ingest(cfg: IngestionConfig) -> InMemoryGraph:
    graph = InMemoryGraph()
    for idx, (title, text, page_id) in enumerate(stream_articles(str(cfg.dump_path))):
        summary = summarize_sections(title, text)
        links = parse_links(text)
        categories = parse_categories(text)
        sources = [f"wikipedia:{page_id}"]
        node = create_node(page_id or str(idx), title, summary, links, categories, sources)
        graph.add_node(node)
        for link in links:
            graph.add_edge(node.node_id, link["target"], link.get("type", "mentions"))
        if (idx + 1) % cfg.commit_interval == 0:
            graph.save()
        if idx >= 9:  # limit for demonstration
            break
    graph.save()
    return graph


__all__ = ["ingest"]
