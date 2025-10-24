# Organic Scripting AI Prototype

This repository sketches a parameter-light, script-driven AI concept aimed at rivaling
conversational assistants such as ChatGPT or Claude while remaining lightweight enough
to run on a personal server. Instead of large neural networks, the system leans on
symbolic knowledge bases, curated heuristics, and continual self-improvement through
rule-guided feedback loops.

## Architecture Overview

* **Knowledge Base** – Markdown documents produced from trusted script corpora and
  online sources. Stored in `runtime/knowledge`.
* **Episodic Memory** – Short-term buffer that tracks recent interactions and their
  evaluated quality.
* **Reasoner** – Rule-driven planner that brainstorms actions, evaluates artifacts,
  and refines memory entries.
* **Training Pipeline** – Bootstraps the knowledge base from curated scripts and
  exports configuration snapshots for auditability.
* **Policy Layer** – YAML rules that guard against biased reinforcement and enforce
  learning restrictions when users provide low-quality feedback.

## Getting Started

### 1. Prepare the Environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # optional placeholder if you extend dependencies
```

### 2. Bootstrap the System

```bash
python scripts/bootstrap.py
```

This populates `runtime/knowledge` with baseline scripts and writes `runtime/config.json`
for reproducibility.

### 3. Run an Interactive Session

```bash
python scripts/run_session.py "Automate deployment pipeline" --keywords "docker ci" \
  --artifact "print('deploy pipeline ready')"
```

The CLI prints the internal thought process, evaluates the provided artifact, records
the experience into episodic memory, and stores the outcome in the knowledge base.

## Extending the Prototype

1. **Trusted Web Growth** – Implement crawlers that fetch content only from URLs listed
   in `ai_system/config.py` and merge verified snippets into the knowledge base.
2. **Self-Correction** – Expand `policies/dialogue_rules.yaml` and wire it into the
   reasoner to detect hollow praise or inconsistent feedback before accepting it.
3. **Evaluator Engines** – Replace the placeholder evaluator with linters, static
   analyzers, or dialogue quality estimators that reward high-quality scripting output.
4. **Server Hosting** – Wrap `ai_system.interfaces.cli.run_session` in a REST or gRPC
   service for multi-user access while persisting runtime data to a mounted volume.

## Disclaimer

This is an experimental blueprint that demonstrates how a parameter-light, script-first
assistant could be composed. It does not match the capabilities of large-scale language
models but serves as a foundation for further research and development.
