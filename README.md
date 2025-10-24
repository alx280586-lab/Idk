# Organic Scripting AI Prototype

The Organic Scripting AI is a parameter-light research prototype that simulates an
"agent with a mind of its own" using curated script corpora, rule-based reasoning,
and incremental knowledge harvesting. It is intentionally lightweight so the full
stack can run on a personal server, yet it still ships with:

* An offline training pipeline that seeds the knowledge base with high-signal
  scripting examples and Grok-style banter.
* An online trainer that learns from whitelisted documentation sites while
  protecting against untrusted sources.
* Multiple operators interfaces: a classic CLI, a Grok-inspired terminal cockpit,
  and a browser control room powered by FastAPI.

This document explains every moving part in enough depth to get the system
running end-to-end on a remote machine with browser access.

---

## Repository Layout

```
.
├── ai_system/                 # Core runtime logic (reasoner, memory, interfaces)
├── corpus/                    # Bootstrap corpora for scripts, conversations, persona
├── policies/                  # Dialogue safeguards and reinforcement rules
├── scripts/                   # Operational scripts (bootstrap, training, servers)
├── web/public/                # Static assets for the browser control room
├── requirements.txt           # Python dependencies
└── README.md                  # This guide
```

The runtime working directory (`./runtime`) is created on demand and holds the
active knowledge base, audit config, and online training state. The folder is
ignored by git so it can grow freely in production.

---

## Prerequisites

* **Python**: 3.10 or newer is recommended.
* **System packages** (optional but helpful): `build-essential`, `libxml2`,
  `libxslt`, and `python3-venv` when deploying on a fresh Linux server.
* **Network access**: outbound HTTPS access to the trusted sources defined in
  `ai_system/config.py` (Python docs and MDN by default).

---

## 1. Create an Isolated Environment

```
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

The dependencies install the Grok terminal renderer (`rich`), the web stack
(`fastapi`, `uvicorn`), and the online scraping toolkit (`requests`,
`beautifulsoup4`).

To leave the environment later, run `deactivate`.

---

## 2. Bootstrap the Knowledge Base

1. **Run the bootstrapper** to materialize the runtime directory:
   ```
   python scripts/bootstrap.py
   ```
2. Confirm the following artifacts were produced:
   * `runtime/config.json` – snapshot of the current configuration.
   * `runtime/knowledge/bootstrap_*.md` – curated scripting patterns and Grok
     persona snippets.
3. Inspect one of the generated Markdown files to verify content:
   ```
   head runtime/knowledge/bootstrap_0001.md
   ```

> **Tip:** If you ever expand the corpora under `corpus/`, rerun the bootstrapper
> to fold the new material into the knowledge cache.

---

## 3. Operate the AI from the Command Line

### Classic CLI

The minimal interface is convenient for piping into shell workflows:

```
python -m ai_system.interfaces.cli "Draft a sarcastic deployment checklist"   --keywords "automation release"
```

You will see:

* The reasoner's internal considerations based on keyword hits.
* A Grok-flavored conclusion with a confidence estimate.
* A newly stored Markdown artifact inside `runtime/knowledge/`.

### Grok Console (Terminal Cockpit)

For the full Grok-inspired experience with mission panels and witty output:

```
python scripts/run_session.py
```

Key bindings and flow:

1. Enter a mission objective when prompted.
2. Supply space-separated keywords to narrow the knowledge search.
3. Review the styled response in the central panel.
4. Decide whether to log the interaction in the knowledge base.
5. Continue launching missions until you exit with `Another mission? [n]`.

The sidebar updates in real time to show recent missions and cached knowledge.

---

## 4. Run the Browser Control Room

The new FastAPI server wraps the same reasoning engine and exposes a Grok-like
control center over HTTP.

1. **Start the server** (bind to all interfaces so remote browsers can connect):
   ```
   python scripts/run_server.py --host 0.0.0.0 --port 8000
   ```
2. **Open the UI** from any browser that can reach the machine:
   ```
   http://<server-ip>:8000/
   ```
3. The interface provides three columns:
   * **Mission Uplink** – submit the goal, optional keywords, and choose whether
     to log the result back into the knowledge cache.
   * **Console Output** – displays the Grok-style response with confidence.
   * **Telemetry** – shows in-memory mission history and the ten most recent
     knowledge files for quick auditing.

Behind the scenes, the UI talks to the following API endpoints:

* `POST /api/missions` – run a new mission.
* `GET /api/history` – retrieve recent memory traces.
* `GET /api/knowledge` – list knowledge files.
* `GET /api/health` – check crawler readiness and knowledge counts.

Because the web server uses the same runtime context as the CLI, missions
launched from the browser immediately influence the Grok console and vice versa.

---

## 5. Enable Online Learning

The online trainer expands the knowledge base with documents fetched from the
trusted sources declared in `ai_system/config.py`.

1. Run a manual harvest:
   ```
   python scripts/train_online.py
   ```
2. Inspect the runtime directory again – new files named `online_<Source>_*` are
   added to `runtime/knowledge/` whenever a crawl succeeds.
3. Each run updates `runtime/online_state.json`, recording the last crawl time
   per source. The helper respects the `crawl_frequency_hours` value so repeated
   invocations do not spam the same site.

### Scheduling on a Server

* **systemd timer (recommended):**
  ```
  # /etc/systemd/system/grok-online.service
  [Unit]
  Description=Grok AI Online Trainer
  After=network.target

  [Service]
  Type=oneshot
  WorkingDirectory=/opt/grok-ai
  ExecStart=/opt/grok-ai/.venv/bin/python scripts/train_online.py
  User=grokai
  Group=grokai
  ```
  ```
  # /etc/systemd/system/grok-online.timer
  [Unit]
  Description=Run Grok AI online trainer hourly

  [Timer]
  OnBootSec=5m
  OnUnitActiveSec=1h

  [Install]
  WantedBy=timers.target
  ```
  Enable with `systemctl enable --now grok-online.timer`.

* **Cron alternative:** `0 * * * * /opt/grok-ai/.venv/bin/python /opt/grok-ai/scripts/train_online.py`

Always monitor the log output to ensure crawls succeed and adjust the trusted
source list if you need additional documentation feeds.

---

## 6. Production Deployment Checklist

1. **Create a dedicated user and directory** (e.g., `/opt/grok-ai`).
2. **Clone the repository** and run the environment setup + bootstrap steps as
   that user.
3. **Harden permissions:**
   * Ownership of `/opt/grok-ai` → `grokai:grokai`.
   * `chmod 700 runtime` so only the service user can read harvested knowledge.
4. **Run the web server under systemd** for resilience:
   ```
   # /etc/systemd/system/grok-server.service
   [Unit]
   Description=Grok AI Control Room
   After=network.target

   [Service]
   WorkingDirectory=/opt/grok-ai
   Environment="PATH=/opt/grok-ai/.venv/bin"
   ExecStart=/opt/grok-ai/.venv/bin/python scripts/run_server.py --host 0.0.0.0 --port 8000
   Restart=on-failure
   User=grokai
   Group=grokai

   [Install]
   WantedBy=multi-user.target
   ```
   Enable with `systemctl enable --now grok-server.service` and confirm via
   `journalctl -u grok-server -f`.
5. **Secure ingress:** put the FastAPI app behind an HTTPS reverse proxy (Nginx,
   Caddy, Traefik) and restrict access to authorized operators.
6. **Back up the runtime folder** regularly – it contains the entire learned
   state.

---

## 7. Customisation & Advanced Usage

* **Extend the persona:** add files to `corpus/conversations/` or edit
  `corpus/persona/profile.yaml`, then rerun `scripts/bootstrap.py`.
* **Fine-tune trusted sources:** edit the `DEFAULT_CONFIG` in
  `ai_system/config.py` to include private documentation or internal wikis.
* **Augment evaluators:** replace the stub scoring functions in
  `ai_system/interfaces/runtime.py` with calls to linters or simulators to reward
  high-quality outputs automatically.
* **Integrate external tooling:** the FastAPI server can be wrapped with
  authentication, rate limiting, or connected to chat platforms by building atop
  the `/api/missions` endpoint.

---

## 8. Troubleshooting

| Symptom | Fix |
| --- | --- |
| `ModuleNotFoundError` for FastAPI or uvicorn | Re-run `pip install -r requirements.txt` in the active virtualenv. |
| Browser shows `UI assets missing` | Ensure `web/public/` exists and the service runs from the repo root. |
| Knowledge count stays at zero | Run `python scripts/bootstrap.py` before launching any interface. |
| Online trainer reports network errors | Verify the server has outbound HTTPS access and adjust firewall rules. |
| Responses feel repetitive | Expand the corpora under `corpus/` and schedule more online harvests. |

---

## 9. Safety Considerations

The AI intentionally resists blind positive reinforcement:

* Dialogue policies live in `policies/dialogue_rules.yaml` – expand them with
  organisation-specific safeguards.
* Online training only touches whitelisted sources to avoid poisoning the
  knowledge base.
* Operators should periodically review new Markdown entries under `runtime/knowledge`
  and prune anything low quality.

With these practices the Organic Scripting AI can grow over time while staying
aligned with your scripting and communication standards.
