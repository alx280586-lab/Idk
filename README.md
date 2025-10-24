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

The checklist below assumes you have a recent version of Python (3.10 or newer) installed. If you are new to Python, follow each step in order and don’t move on until the previous command succeeds.

1. **Download the project**

   ```bash
   git clone <this-repo-url>
   cd Idk  # or the folder name you chose when cloning
   ```

2. **Create and activate a virtual environment**

   A virtual environment keeps the project’s dependencies separate from the rest of your system.

   ```bash
   python -m venv .venv
   # macOS / Linux
   source .venv/bin/activate
   # Windows PowerShell
   # .venv\Scripts\Activate.ps1
   ```

   After activation your terminal prompt should show `(.venv)` at the beginning.

3. **Install Python dependencies**

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

   If a package fails to install, read the error message and install any missing system tools (for example, `pip install wheel` on Windows before re-running the command).

4. **Review configuration files**

   - `config.yaml` – change `allowed_sources` to the documentation sites you trust. The retrieval module will refuse to fetch from domains not listed here.
   - `persona.yaml` – adjust the `name`, tone keywords, and phrases to shape how the chatbot speaks.
   - `heuristics.yaml` – optional; stores style preferences learned from training. Delete it to reset the lab’s memory.

5. **Provide initial examples (optional but recommended)**

   Place Luau scripts you like in `data/examples/` and describe tests in JSON files inside `data/tests/`. The default `spawn.lua`/`spawn_test.json` pair demonstrates the format.

6. **Run the training pass**

   Training ingests the examples/tests and updates `heuristics.yaml`.

   ```bash
   python -m luau_lab.training
   ```

   You should see log messages confirming which examples were scanned. Rerun this command whenever you add or modify examples.

## Running the chatbot (CLI)

```bash
python main.py
```

- The CLI automatically loads the persona, heuristics, and allowed documentation sources you configured during setup.
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

If you want the lab to forget what it has learned, delete `heuristics.yaml` and rerun the command above.

## Extending the lab

- Add new templates in `luau_lab/synthesizer.py` to cover more Roblox systems.
- Expand persona phrases in `persona.yaml` to adjust the lab’s voice.
- Create additional example scripts/tests to steer the generator toward your project’s patterns.

## Hosting considerations

The web server provided here is a lightweight Flask app intended for local or LAN access. If you want to host it publicly, place it behind HTTPS (e.g., via nginx) and protect the endpoints with authentication to avoid misuse.

For quick remote demos, you can run the server locally and tunnel it with a tool such as `ngrok` or `cloudflared tunnel`—just be mindful that this exposes your workstation to the internet, so enable authentication first.

## License

This repository is provided as-is for experimentation with local-first AI assistants.
