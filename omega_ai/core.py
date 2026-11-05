"""Provider-independent local AI engine.

The engine talks to a locally running Ollama-compatible HTTP endpoint.
It stores conversation history locally and does not require ChatGPT.
"""
from __future__ import annotations

import json
import os
import sqlite3
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_ENDPOINT = "http://127.0.0.1:11434/api/chat"
DEFAULT_MODEL = "qwen2.5:1.5b"
DB_PATH = Path.home() / ".omega_ai" / "memory.sqlite3"


class OmegaAIError(RuntimeError):
    pass


def _db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    return conn


def remember(role: str, content: str) -> None:
    if role not in {"user", "assistant"}:
        raise ValueError("Unsupported memory role")
    with _db() as conn:
        conn.execute("INSERT INTO messages(role, content) VALUES (?, ?)", (role, content))


def recent_messages(limit: int = 12):
    with _db() as conn:
        rows = conn.execute(
            "SELECT role, content FROM messages ORDER BY id DESC LIMIT ?",
            (max(1, min(limit, 40)),),
        ).fetchall()
    return [{"role": role, "content": content} for role, content in reversed(rows)]


def ask(prompt: str, model: str | None = None, endpoint: str | None = None) -> str:
    prompt = prompt.strip()
    if not prompt:
        raise ValueError("Prompt cannot be empty")

    endpoint = endpoint or os.getenv("OMEGA_AI_ENDPOINT", DEFAULT_ENDPOINT)
    model = model or os.getenv("OMEGA_AI_MODEL", DEFAULT_MODEL)
    messages = [
        {
            "role": "system",
            "content": (
                "You are OMEGA AI CORE, an independent local software assistant. "
                "Be accurate, explain uncertainty, protect private data, and support "
                "authorized security testing and isolated simulations."
            ),
        },
        *recent_messages(),
        {"role": "user", "content": prompt},
    ]
    # llama.cpp server exposes the OpenAI-compatible route; Ollama uses /api/chat.
    openai_compatible = endpoint.rstrip("/").endswith("/v1/chat/completions")
    payload_data = {"model": model, "messages": messages, "stream": False}
    payload = json.dumps(payload_data).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise OmegaAIError(
            "Cannot reach the local model server. Start Ollama or llama-server, "
            "then check OMEGA_AI_ENDPOINT and OMEGA_AI_MODEL."
        ) from exc

    if openai_compatible:
        choices = data.get("choices") or []
        message = choices[0].get("message", {}) if choices else {}
        answer = message.get("content", "")
    else:
        answer = data.get("message", {}).get("content", "")
    answer = answer.strip() if isinstance(answer, str) else ""
    if not answer:
        raise OmegaAIError("The local model returned an empty response.")
    remember("user", prompt)
    remember("assistant", answer)
    return answer


def status() -> dict:
    return {
        "engine": "OMEGA AI CORE",
        "provider": "local HTTP endpoint (Ollama or llama.cpp)",
        "endpoint": os.getenv("OMEGA_AI_ENDPOINT", DEFAULT_ENDPOINT),
        "model": os.getenv("OMEGA_AI_MODEL", DEFAULT_MODEL),
        "memory": str(DB_PATH),
    }
