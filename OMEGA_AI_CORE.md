# OMEGA AI CORE

A standalone Python assistant engine that uses a local Ollama-compatible model endpoint.
It does not use ChatGPT APIs and stores its conversation history in a local SQLite database.

## Requirements

- Python 3.10+
- Ollama installed and running locally
- A model downloaded in Ollama

## Setup

Install Ollama for your platform, start the Ollama service, then download a small model:

    ollama pull qwen2.5:1.5b

From the project root:

    python main.py ai-status
    python main.py ai-ask "اشرح لي بنية مشروع Python"

Optional environment settings:

    OMEGA_AI_ENDPOINT=http://127.0.0.1:11434/api/chat
    OMEGA_AI_MODEL=qwen2.5:1.5b

The first model download requires internet. After the model is present locally, inference can run offline.
On Android, local model execution depends on available RAM, CPU, storage, and whether a compatible Ollama build is available; a desktop or separate local server may be needed.

## Independence

The engine has its own provider endpoint, model selection, and SQLite memory.
It is a separate software component, not a modification of ChatGPT or its policies.
