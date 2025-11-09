# Mycelium-Roblox

Mycelium-Roblox is a lightweight research scaffold that demonstrates a
Planner–Actor–Critic workflow tailored for Roblox automation tasks. The
system is intentionally offline-friendly while keeping clear extension
points for integrating a local LLaMA model and richer Roblox tools.

## Project layout

```
config.yaml              # Runtime configuration (model, memory, tooling)
mycelium_roblox/
  __init__.py
  actor.py               # Actor agent generating Lua scripts
  critic.py              # Critic agent running lint/sandbox/tests
  memory.py              # SQLite-backed memory store
  planner.py             # Planner agent creating multi-step plans
  run.py                 # Entry point orchestrating the learning loop
  tools.py               # Local tooling stubs (LLM, linter, sandbox, etc.)
```

## Getting started

Create a Python 3.11 virtual environment and install the repository in
editable mode if desired. The entry point can then be executed directly:

```bash
python -m mycelium_roblox.run
```

On completion the program prints diagnostics summarising the plan,
actions, and critic feedback for the bundled radar visualisation task.
The generated Lua code is stored in the SQLite memory at
`mycelium_roblox/memory.db` for future retrieval.
