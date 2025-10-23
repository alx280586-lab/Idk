"""Flask server exposing the Luau Synthesis Lab over HTTP."""
from __future__ import annotations

from flask import Flask, jsonify, request

from luau_lab import load_config
from luau_lab.dialogue import DialogueEngine
from luau_lab.synthesizer import LuauSynthesizer
from luau_lab.training import TrainingSuite
from luau_lab.retrieval import RetrievalClient

app = Flask(__name__)

_config = load_config()
_trainer = TrainingSuite(_config)
_synthesizer = LuauSynthesizer(_trainer.heuristics)
_retriever = RetrievalClient(_config.allowed_sources)
_engine = DialogueEngine(
    config=_config,
    synthesizer=_synthesizer,
    retriever=_retriever,
    trainer=_trainer,
)


@app.post("/api/chat")
def chat_endpoint():
    payload = request.get_json(force=True)
    message = payload.get("message", "")
    reply = _engine.respond(message)
    _engine.remember(message, reply)
    return jsonify({"reply": reply})


@app.post("/api/train")
def train_endpoint():
    summary = _trainer.run_all()
    return jsonify(summary)


@app.post("/api/doc")
def doc_endpoint():
    payload = request.get_json(force=True)
    url = payload.get("url", "")
    query = payload.get("query", "")
    try:
        result = _retriever.fetch(url, query)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    return jsonify({"source": result.source, "snippets": result.snippets})


@app.get("/")
def index():
    persona_name = _engine.persona.get("name", "Lab")
    greeting = _engine._persona_pick("greeting", "Hello! Ready to build?")
    return f"""
<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <title>Luau Synthesis Lab</title>
  <style>
    body {{ font-family: sans-serif; max-width: 720px; margin: 2rem auto; }}
    #log {{ white-space: pre-wrap; border: 1px solid #ccc; padding: 1rem; height: 320px; overflow-y: auto; }}
    form {{ display: flex; gap: 0.5rem; margin-top: 1rem; }}
    input[type=text] {{ flex: 1; padding: 0.5rem; }}
    button {{ padding: 0.5rem 1rem; }}
  </style>
</head>
<body>
  <h1>{persona_name} – Luau Synthesis Lab</h1>
  <p>{greeting}</p>
  <div id=\"log\"></div>
  <form id=\"chat-form\">
    <input type=\"text\" id=\"message\" placeholder=\"Ask for a Roblox script...\" required />
    <button type=\"submit\">Send</button>
  </form>
  <script>
    const log = document.getElementById('log');
    document.getElementById('chat-form').addEventListener('submit', async (event) => {{
      event.preventDefault();
      const messageInput = document.getElementById('message');
      const message = messageInput.value;
      log.textContent += `You> ${message}\n`;
      messageInput.value = '';
      const response = await fetch('/api/chat', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ message }})
      }});
      const data = await response.json();
      log.textContent += `{persona_name}> ${data.reply}\n\n`;
      log.scrollTop = log.scrollHeight;
    }});
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
