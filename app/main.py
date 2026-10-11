#!/usr/bin/env python3
import os
import json
import time
import requests
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)
import markdown2
import bleach
from markupsafe import Markup

app = Flask(__name__)

# ---------- Konfiguration ----------
app.secret_key = os.getenv("FLASK_SECRET_KEY", "changeme-please")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
_RESPONSE_TIMEOUT_STR = os.getenv("RESPONSE_TIMEOUT", "600")
try:
    RESPONSE_TIMEOUT = float(_RESPONSE_TIMEOUT_STR)  # 600.0s → 10min
except (TypeError, ValueError):
    # Fallback, falls die Umgebungsvariable keinen gültigen Zahlwert enthält
    RESPONSE_TIMEOUT = 600.0

# ---- Caching‑Mechanismus für Modell‑Liste ----
_MODEL_CACHE = {"timestamp": 0, "models": []}
_CACHE_TTL = 60  # Sekunden

# --------------------------------------------------------------------
#  Jinja‑Filter für Markdown
# --------------------------------------------------------------------
@app.template_filter('markdown2')
def markdown2_filter(text: str) -> Markup:
    html = markdown2.markdown(text, extras=["safe_mode"])
    cleaned = bleach.clean(html, tags=bleach.sanitizer.ALLOWED_TAGS, attributes=bleach.sanitizer.ALLOWED_ATTRIBUTES)
    return Markup(cleaned)

def _fetch_models_from_ollama() -> list[str]:
    """
    Ruft die aktuell installierten Modelle von Ollama ab.
    Rückgabe: Liste von Modell‑Names
    """
    url = f"{OLLAMA_HOST}/api/tags"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return [m["name"] for m in data.get("models", [])]
    except Exception as exc:
        app.logger.error("Fehler beim Abrufen der Modelle: %s", exc)
        return []

def call_ollama(model: str, prompt: str) -> str:
    """
    Sendet einen Prompt an Ollama und gibt die Antwort zurück.
    """
    url = f"{OLLAMA_HOST}/api/chat"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }
    try:
        resp = requests.post(url, json=payload, timeout=RESPONSE_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        # Ollama liefert Antwort in data["message"]["content"]
        content = data["message"]["content"]

        # 2. Optional: falls die Antwort bereits Markdown ist, keine Konvertierung
        #    Falls du die Antwort in reinen HTML‑Text umwandeln möchtest, schreibe:
        #content = markdown2.markdown(content)
        return content
    except Exception as exc:
        app.logger.error("Ollama‑Error: %s", exc)
        return f"[Fehler beim Aufruf von Ollama: {exc}]"

def get_available_models() -> list[str]:
    """
    Liefert die aktuelle Modell‑Liste unter Nutzung des Cache.
    """
    now = time.time()
    if now - _MODEL_CACHE["timestamp"] > _CACHE_TTL:
        _MODEL_CACHE["models"] = _fetch_models_from_ollama()
        _MODEL_CACHE["timestamp"] = now
    return _MODEL_CACHE["models"]

# ---------- Flask‑Routen ----------
@app.before_request
def set_default_session():
    """Session‑Initialisierung – stellt sicher, dass ein Verlauf und ein Modell vorhanden sind."""
    session.setdefault("history", [])
    available = get_available_models()
    # Fallback, falls Ollama momentan keine Modelle liefert
    session.setdefault("model", available[0] if available else "n/a")

@app.route("/", methods=["GET"])
def index():
    available = get_available_models()
    # Falls kein Modell verfügbar, UI‑Error‑Message zeigen
    if not available:
        flash("Keine LLM‑Modelle auf dem Ollama‑Server gefunden.", "warning")
    return render_template(
        "chat.html",
        history=session["history"],
        models=available,
        current_model=session.get("model", "n/a"),
    )

@app.route("/chat", methods=["POST"])
def chat():
    prompt = request.form.get("prompt", "").strip()
    model = request.form.get("model", "")

    if not prompt:
        flash("Bitte einen Prompt eingeben.", "warning")
        return redirect(url_for("index"))

    # Nur ein gültiges Modell aus der aktuellen Liste zulassen
    available = get_available_models()
    if model not in available:
        flash(f"Modell '{model}' ist nicht auf dem Ollama‑Server installiert.", "danger")
        return redirect(url_for("index"))

    session["model"] = model

    # --- Prompt an Ollama schicken ----
    answer = call_ollama(model, prompt)

    # Verlauf aktualisieren
    session["history"].append({"role": "user", "content": prompt})
    session["history"].append({"role": "assistant", "content": answer})

    return redirect(url_for("index"))

@app.errorhandler(500)
def internal_error(error):
    app.logger.error("Serverfehler: %s", error)
    flash("Ein unerwarteter Fehler ist aufgetreten.", "danger")
    return redirect(url_for("index"))

# ---------- Haupt‑Funktion ----------
if __name__ == "__main__":
    # Für Produktionsumgebungen ist ein Reverse‑Proxy mit TLS empfohlen.
    app.run(host="0.0.0.0", port=5002, debug=False)
