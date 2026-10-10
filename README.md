# Simple-LLM‑Chat

Ein einfacher Chat‑Client für Ollama‑LLM‑Modelle, der in Docker betrieben wird.

## Voraussetzungen

* Docker lokal
* Ollama remote oder lokal

## Konfiguration

| Variable | Zweck                        | Beispiel                           |
|----------|------------------------------|------------------------------------|
| `OLLAMA_HOST` | Ollama‑Endpoint (inkl. Port) | `http://<ollama_ip>:<ollama_port>` |
| `RESPONSE_TIMEOUT` | Ollama Response Timeout      | `600`                              |
| `FLASK_SECRET_KEY` | Flask‑Session‑Secret         | `supersecretkey123`                |

## Start
```bash
docker run -d -p "5002:5002" \
-e OLLAMA_HOST=http://<ollama_ip>:<ollama_port> \
-e RESPONSE_TIMEOUT=600 \
-e FLASK_SECRET_KEY=<zufällige_zeichenkette> \
--name simple_llm_chat \
<docker_image_name>
```

#### Mögliche Werte für <docker_image_name>:
    ghcr.io/creadesk/simple_llm_chat:latest

    codeberg.org/creadesk/simple_llm_chat:latest

## Aufruf
```
http://127.0.0.1/5002
```