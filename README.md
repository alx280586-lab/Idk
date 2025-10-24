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

The guide below walks through every step, including where to download the software you need. Follow the steps in order and stop if something fails so you can fix it before moving on.

### 0. Install the tools you need (do this once)

| Tool | Why you need it | Where to get it |
| ---- | --------------- | --------------- |
| **Python 3.10 or newer** | Runs the chatbot. | https://www.python.org/downloads/ — on Windows tick **Add python.exe to PATH** during installation. |
| **Git** (optional but recommended) | Makes it easy to download the project and pull updates later. | https://git-scm.com/downloads |
| **Text editor** | Lets you edit `.yaml` and `.lua` files. | Visual Studio Code (https://code.visualstudio.com/) or any editor you like. |

After installing Python, open a **new** terminal or Command Prompt and check it works:

```bash
python --version
```

If the command prints a version number (for example `Python 3.11.8`) you are ready. If it says the command is unknown, restart your computer or reinstall Python and ensure the “Add to PATH” option is enabled.

### 1. Download the project files

You can grab the files with Git or by downloading a ZIP. Pick whichever you prefer.

**Option A – Git clone (best for updates)**

1. Open a terminal (Windows: search for **PowerShell**; macOS: open the **Terminal** app).
2. Move to the folder where you want the project to live:

   ```bash
   cd C:\Projects    # Windows example path
   # or
   cd ~/Projects      # macOS/Linux example path
   ```

3. Download the project and enter the new folder:

   ```bash
   git clone <this-repo-url>
   cd Idk
   ```

**Option B – download ZIP (no Git needed)**

1. Visit the repository page in your web browser.
2. Click **Code ▾ → Download ZIP**.
3. Extract the ZIP (Windows: right-click → **Extract All…**; macOS: double-click the ZIP).
4. Open a terminal and change into the extracted folder:

   ```bash
   cd path/to/extracted/folder
   ```

From this point on all commands should be run from inside the project folder you just opened.

### 2. Create and activate a virtual environment

This isolates the project’s Python packages so they do not affect other software on your computer.

```bash
python -m venv .venv
```

Activate it using the command that matches your platform:

```bash
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Windows Command Prompt (cmd.exe)
.\.venv\Scripts\activate.bat

# macOS / Linux
source .venv/bin/activate
```

You should now see `(.venv)` at the beginning of your terminal prompt. Keep the terminal open while you work; closing it deactivates the environment and you will need to run the activation command again in a new session.

### 3. Install the Python dependencies

With the virtual environment active, install the required packages:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If an error mentions missing build tools, install the tool it suggests (for example **Visual Studio Build Tools** on Windows) and then run the command again.

### 4. Review and customise the configuration files

Open these files in your text editor and adjust them to match how you want the bot to behave:

- **`config.yaml`** – update the `allowed_sources` list with the full URLs of the documentation sites you trust (e.g. `https://create.roblox.com/docs/`). The retriever refuses to access sites not listed here.
- **`persona.yaml`** – set the bot’s `name`, tone keywords, and example phrases so the dialogue sounds the way you prefer.
- **`heuristics.yaml`** – stores preferences learned from training. You can leave it alone initially; delete it later if you want to reset the bot’s memory.

Save the files after editing them. The chatbot loads these files each time it starts.

### 5. Add example scripts and tests (optional but recommended)

1. Copy Luau scripts you like into the `data/examples/` folder. The provided `spawn.lua` file shows the expected format.
2. (Optional) Add JSON files inside `data/tests/` to describe how the scripts should behave. The sample `spawn_test.json` file demonstrates the structure.

You can skip this step at first and come back later when you have your own scripts to teach the bot.

### 6. Run the training pass

Training scans the examples/tests and updates `heuristics.yaml`.

```bash
python -m luau_lab.training
```

Keep the virtual environment activated while running this command. The terminal output should mention each example that was processed. Rerun training whenever you add or change example files.

## Running the chatbot (CLI)

1. Open a terminal **inside the project folder**.
2. Activate the virtual environment again if your prompt does not already show `(.venv)` (see the activation commands in [Step 2](#2-create-and-activate-a-virtual-environment)).
3. Start the chatbot:

   ```bash
   python main.py
   ```

4. Type your request, for example: `Make a script that picks a random spawn tagged NPC and explain it.`
5. When you finish, enter `quit` or press `Ctrl+C` to close the program.

Tips:

- The CLI automatically loads your persona, heuristics, and allowed documentation settings every time it launches.
- Type `train` during a session to run the training suite again after you change any example files.
- The last few messages are saved in `session.json` so you can review what the bot generated.

## Running the web server

The web server lets you talk to the bot through your browser. It uses the same files and settings as the CLI.

1. Open a new terminal in the project folder and activate the virtual environment (`source .venv/bin/activate` on macOS/Linux or `.\.venv\Scripts\Activate.ps1` on Windows PowerShell).
2. Start the server:

   ```bash
   python web_server.py
   ```

3. Keep the terminal open. You now have two ways to reach the chat UI:

   - **Open the bundled `index.html` file** – double-click `index.html` (or open it via `File → Open File…` in your browser).
     The page connects to the running server at `http://127.0.0.1:8000` automatically. This is the easiest option if you prefer
     launching the UI from your desktop or file manager.
   - **Visit the live server** – open your browser and go to `http://localhost:8000`. The Flask app serves the same `index.html`
     file directly.

4. Chat with the bot using either window. When you are done, return to the terminal and press `Ctrl+C` to stop the server.

The server also exposes JSON endpoints if you want to integrate another tool:

- `POST /api/chat` – `{ "message": "..." }`
- `POST /api/train` – triggers the training suite.
- `POST /api/doc` – `{ "url": "https://create.roblox.com/docs/...", "query": "PathfindingService" }`

## Turn it into an “app” with the quick-launch UI

If you want a point-and-click experience, use the `start_ui.py` launcher. It starts the training pass (optional), boots the web server, and opens your browser automatically so you land directly in the chatbot UI.

### Step-by-step (Windows, macOS, or Linux)

1. Make sure your virtual environment is active (see [Step 2](#2-create-and-activate-a-virtual-environment)).
2. Run the launcher:

   ```bash
   python start_ui.py
   ```

   The script prints the server address (default `http://127.0.0.1:8000`) and then opens your default browser to that page. Leave the terminal window open while you use the app. Press `Ctrl+C` in the terminal when you want to shut it down.

3. (Optional) Have the launcher retrain before opening the UI:

   ```bash
   python start_ui.py --train
   ```

4. (Optional) If you prefer to start the server first and open the browser yourself, add `--no-browser`:

   ```bash
   python start_ui.py --no-browser
   ```

### Create a desktop shortcut (optional)

- **Windows:**
  1. Open Notepad and paste `@echo off` on the first line and `call %~dp0\.venv\Scripts\activate.bat` on the second line, followed by `python start_ui.py` on the third line.
  2. Save the file as `StartLuauLab.bat` inside the project folder.
  3. Right-click the new file → **Create shortcut** and move the shortcut to your desktop. Double-click it whenever you want to launch the chatbot UI.

- **macOS/Linux:**
  1. Create a file called `start_luau_lab.sh` in the project folder with the contents:

     ```bash
     #!/usr/bin/env bash
     source "$(dirname "$0")/.venv/bin/activate"
     python "$(dirname "$0")/start_ui.py"
     ```

  2. Make it executable:

     ```bash
     chmod +x start_luau_lab.sh
     ```

  3. Drag the file into your dock/launcher or double-click it from your file manager (choose “Run in Terminal” when prompted).

This approach keeps everything local and avoids extra steps—once your environment is prepared, launching the UI is as simple as double-clicking your shortcut.

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

## Using documentation retrieval

1. Add every site you trust to the `allowed_sources` list in `config.yaml` (include the `https://` part). Example:

   ```yaml
   allowed_sources:
     - "https://create.roblox.com/docs/"
     - "https://devforum.roblox.com/"
   ```

2. In the CLI or web chat, type `doc <url> <search words>`.

   ```text
   doc https://create.roblox.com/docs/ PathfindingService
   ```

3. The bot prints bullet-point snippets from that page. If the URL is not whitelisted, you will see a message saying it was blocked.

This feature only reads the pages you explicitly allow and never follows other links.

## Everyday workflow example

1. Start your virtual environment and run `python main.py`.
2. Ask for a script: `Can you write a Luau function that picks a random SpawnLocation tagged NPC?`
3. Copy the code between the triple backticks (` ```lua ... ``` `) into a new Script or ModuleScript in Roblox Studio.
4. Read the explanation lines below the code to understand what each part does.
5. If you adjust the generated code manually and want the bot to learn your style, save it in `data/examples/` and rerun `python -m luau_lab.training`.
6. Use the `doc` command whenever you need reminders from the Roblox documentation.

## Troubleshooting

| Problem | What it means | How to fix it |
| ------- | -------------- | ------------- |
| `python` is not recognized | Python is not on your PATH. | Reinstall Python from python.org and check **Add python.exe to PATH**, then restart your terminal. |
| `pip` errors about build tools | A package needs compilers. | Install the suggested tool (for example **Visual Studio Build Tools** on Windows) and run `pip install -r requirements.txt` again. |
| `ModuleNotFoundError` when running `python main.py` | Virtual environment was not activated. | Run the activation command (`.\.venv\Scripts\Activate.ps1` or `source .venv/bin/activate`) before running Python commands. |
| Browser cannot reach `http://localhost:8000` | The server is not running. | Check the terminal that started `python web_server.py` for errors and keep it open while you access the page. |
| `Address already in use` when starting the web server | Something else is using port 8000. | Stop the other program or edit `web_server.py` to use a different port (change the `port=8000` value). |

## Extending the lab

- Add new templates in `luau_lab/synthesizer.py` to cover more Roblox systems.
- Expand persona phrases in `persona.yaml` to adjust the lab’s voice.
- Create additional example scripts/tests to steer the generator toward your project’s patterns.

## Hosting considerations

The web server provided here is a lightweight Flask app intended for local or LAN access. If you want to host it publicly, place it behind HTTPS (e.g., via nginx) and protect the endpoints with authentication to avoid misuse.

For quick remote demos, you can run the server locally and tunnel it with a tool such as `ngrok` or `cloudflared tunnel`—just be mindful that this exposes your workstation to the internet, so enable authentication first.

## License

This repository is provided as-is for experimentation with local-first AI assistants.
