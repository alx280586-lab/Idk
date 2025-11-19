# Neural-Field Cognitive Engine (NFCE)

NFCE is an experimental reference implementation of a non-transformer cognitive architecture. This repository provides a self-contained skeleton capable of ingesting Wikipedia content, mapping it into richly typed knowledge graph nodes, projecting language into a neural semantic field, and generating conversational responses with a lightweight adapter. The implementation prioritizes readability and modularity so that each subsystem can be iterated independently.

## Highlights
- **Semantic Field:** Compact Fourier-style operator with damping and patch networks to demonstrate continuous dynamics.
- **Knowledge Graph:** Pydantic node schema aligned with the gravity example, stored in an in-memory graph for development.
- **Ingestion Pipeline:** End-to-end stub that parses XML dumps, extracts links and categories, and constructs nodes.
- **Reasoning Engine:** Orchestrates projection, propagation, retrieval, and conversational response generation.
- **Documentation:** Mermaid diagrams and a short training cookbook to guide experimentation.

## Quickstart
```bash
pip install -r requirements.txt
python src/scripts/chat_demo.py
```

## Repository Layout
- `src/nfce/semantic_field/` — field model, propagator, losses, patch networks.
- `src/nfce/knowledge_graph/` — node schema, graph persistence, retrieval, and updates.
- `src/nfce/ingestion/` — Wikipedia parsing utilities and pipeline entry point.
- `src/scripts/` — runnable scripts for ingestion, training phases, demo, and manual node insertion.
- `docs/` — diagrams and cookbook.

## Ingestion Overview
The ingestion pipeline streams articles from a compressed XML dump, performs lightweight structural parsing to collect links and categories, invokes a stub meaning extractor, and materializes `Node` objects. The resulting graph is written to `data/processed_graph/graph.json` for inspection. Replace the stub summarizer with a real LLM-backed parser to scale to full Wikipedia dumps.

## Training Phases
1. **Phase 1:** Build the graph: `python src/scripts/train_phase1_build_graph.py`
2. **Phase 2:** Align the semantic field: `python src/scripts/train_phase2_field_alignment.py`
3. **Phase 3:** Adapt the conversational module: `python src/scripts/train_phase3_conversation.py`

## Future Work
- Swap the in-memory graph for Neo4j + FAISS.
- Expand the semantic field to 2D/3D grids with richer operators.
- Integrate real emotion, sarcasm, and contradiction models.
- Add evaluation suites mirroring the three training phases.
