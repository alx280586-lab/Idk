# Luau Synthesis Lab

A laptop-friendly Roblox scripting assistant that generates Luau code, explains every line, trains on your local examples, and retrieves documentation from a whitelisted set of websites. Everything runs locally in Python – no large language models or external datastores required.

## Features

- **Chatbot CLI and web UI** – talk to the lab from your terminal or browser.
- **Template-driven Luau generator** – request spawn/teleport/storm helpers and receive working scripts with explanations.
- **One-file training suite** – mine your `data/examples` and `data/tests` to keep heuristics aligned with your codebase.
- **Doc retrieval** – supply trusted documentation URLs; the lab will pull contextual snippets on demand.
- **Session memory** – the last few turns are written to `session.json` for review and debugging.

## Project layout

```
luau_lab/
  __init__.py
  config.py
  dialogue.py
  retrieval.py
  synthesizer.py
  training.py
config.yaml
heuristics.yaml
persona.yaml
main.py
web_server.py
data/
  examples/
    spawn.lua
  tests/
    spawn_test.json
requirements.txt
```

## Setup

1. **Install dependencies**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use `.venv\\Scripts\\activate`
   pip install -r requirements.txt
   ```

2. **(Optional) Update allowed documentation sources**

   Edit `config.yaml` and modify the `allowed_sources` list. Any URL prefix you add here becomes available to the retrieval module.

3. **Provide training examples**

   Drop Luau/Luau scripts into `data/examples/` and test descriptors (`.json`) into `data/tests/`. Run the training command (see below) to ingest them.

## Running the chatbot (CLI)

```bash
python main.py
```

- Type your request, e.g., `Make a script that picks a random spawn tagged NPC and explain it.`
- Use the command `train` to re-run the training suite and update heuristics from the latest examples.
- Exit with `quit` or `exit`.

## Running the web server

```bash
python web_server.py
```

Visit `http://localhost:8000` in your browser to chat with the lab. The server also exposes JSON endpoints:

- `POST /api/chat` – `{ "message": "..." }`
- `POST /api/train` – triggers the training suite.
- `POST /api/doc` – `{ "url": "https://create.roblox.com/docs/...", "query": "PathfindingService" }`

## Training suite (single entry point)

All training logic lives in `luau_lab/training.py`. To run it manually:

```bash
python -m luau_lab.training
```

The suite performs three passes:

1. Scans example scripts to detect naming conventions and preferences (e.g., `Random.new` vs `math.random`).
2. Reads JSON test descriptors to surface expectations the generator should satisfy.
3. Loads persona settings to keep dialogue consistent.

Updated heuristics are persisted to `heuristics.yaml`.

## Extending the lab

- Add new templates in `luau_lab/synthesizer.py` to cover more Roblox systems.
- Expand persona phrases in `persona.yaml` to adjust the lab’s voice.
- Create additional example scripts/tests to steer the generator toward your project’s patterns.

## Hosting considerations

The web server provided here is a lightweight Flask app intended for local or LAN access. If you want to host it publicly, place it behind HTTPS (e.g., via nginx) and protect the endpoints with authentication to avoid misuse.

## License

This repository is provided as-is for experimentation with local-first AI assistants.
