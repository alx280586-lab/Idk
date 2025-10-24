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
pip install -r requirements.txt
```

The dependencies enable the Grok-style UI (`rich`) and the online harvester
(`requests` + `beautifulsoup4`).

### 2. Bootstrap Offline Knowledge

```bash
python scripts/bootstrap.py
```

This populates `runtime/knowledge` with curated scripting playbooks and conversation
exercises (including the Grok voice primer) while writing `runtime/config.json` for
auditability.

### 3. Schedule Online Growth

```bash
python scripts/train_online.py
```

The online trainer crawls the whitelisted sources defined in `ai_system/config.py`,
extracts readable text, and stores it as Markdown entries. Re-run this command manually
or schedule it with `cron`/`systemd` to keep the AI learning from trusted articles.

### 4. Launch the Grok Console

```bash
python scripts/run_session.py
```

You will be dropped into a full-screen Grok-inspired interface:

1. Enter a mission goal (e.g., "Craft a sarcastic deployment checklist").
2. Provide keywords so the planner can surface targeted knowledge.
3. Review the cheeky response and optional knowledge log entry.
4. Accept or skip logging to reinforce good behaviors in the knowledge base.

The UI mirrors Grok's attitude—quick wit, high signal, and confident call-to-action
endings—thanks to the enriched persona and corpus additions.

## Server Deployment Blueprint

1. **Provision a Service User** – Create a dedicated Unix user (e.g., `grokai`) and
   clone this repo inside `/opt/grok-ai` with the runtime directory mounted on fast
   storage.
2. **Create a Virtual Environment** – Use the commands above under that user. Install
   optional OS packages such as `libxml2` if your online sources require richer HTML
   parsing.
3. **Persist Runtime Data** – Ensure `/opt/grok-ai/runtime` is writable. Back it up or
   mount it on network storage so online learning survives restarts.
4. **Automate Training** – Add a `systemd` timer or cron entry invoking
   `python /opt/grok-ai/scripts/train_online.py` hourly. Logs will list new knowledge
   files so you can audit growth.
5. **Expose the UI** – Run `python /opt/grok-ai/scripts/run_session.py` within `tmux`
   or `screen` for administrators, or wrap the reasoner in a thin FastAPI/Flask layer
   if you want multi-tenant web access.
6. **Secure Feedback Loops** – Monitor `policies/dialogue_rules.yaml` and expand it
   with organization-specific guardrails so the AI resists manipulative praise while
   still adapting to constructive critique.

## Extending the Prototype

1. **Self-Correction Enhancements** – Plug evaluation commands (linters, test suites)
   into `config.py` so the reasoner can reward scripts that compile and pass checks.
2. **Dialogue Studio** – Expand the persona corpus in `corpus/conversations/` with
   more Grok-level banter, ensuring each entry ends with an actionable nudge.
3. **Analytics Dashboard** – Tailor the Grok console or expose metrics (missions per
   hour, confidence trends) via Prometheus/Grafana for operators monitoring growth.

## Disclaimer

This is an experimental blueprint that demonstrates how a parameter-light, script-first
assistant could be composed. It does not match the capabilities of large-scale language
models but serves as a foundation for further research and development.
