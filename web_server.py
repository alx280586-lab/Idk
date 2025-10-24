from __future__ import annotations

from flask import Flask, jsonify, request, send_from_directory

from luau_lab import load_config
from luau_lab.dialogue import DialogueEngine
from luau_lab.retrieval import RetrievalClient
from luau_lab.synthesizer import LuauSynthesizer
from luau_lab.training import TrainingSuite

app = Flask(__name__)

_config = load_config()
_retriever = RetrievalClient(_config.get_allowed_sources())
_trainer = TrainingSuite(_config, retriever=_retriever)
_synthesizer = LuauSynthesizer(_trainer.heuristics)
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
    return send_from_directory(".", "index.html")


@app.get("/api/persona")
def persona_endpoint():
    return jsonify(
        {
            "name": _engine.persona.get("name", "Lab"),
            "greeting": _engine._persona_pick("greeting", "Hello! Ready to build?"),
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
