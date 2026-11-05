# THE SPIDER OMEGA

Python security-testing toolkit with a standalone local AI component, **OMEGA AI CORE**.

## Features

- Offline URL heuristic analysis and phishing-message analysis.
- Authorized private-lab TCP checks.
- Passive DNS, TLS and HTTP security-header inspection.
- Non-invasive website configuration and exposure assessment.
- Local Python source audit for risky SQL construction.
- Isolated in-memory SQL injection training demonstration.
- Local SQLite table export.
- JSON and Markdown reports.
- OMEGA AI CORE: local-model chat through an Ollama-compatible endpoint, with SQLite conversation memory.

## Install on Termux

    pkg update && pkg upgrade -y
    pkg install python git -y
    git clone https://github.com/hakeemqq1998pp-cell/HKA.1.1.1.1.git
    cd HKA.1.1.1.1

The project core uses the Python standard library. No `pip install` step is required for the built-in commands.

## Basic commands

    python main.py --help
    python main.py scan-url https://example.com
    python main.py analyze-email --text "Your account needs attention"
    python main.py recon example.com
    python main.py web-audit https://example.com
    python main.py vuln-scan https://example.com
    python main.py sql-audit --path .
    python main.py injection-lab
    python main.py history

Only run active checks against systems you own or are explicitly authorized to test.

## OMEGA AI CORE

OMEGA AI CORE is a separate local Python component. It does not call ChatGPT APIs.
It supports Ollama's /api/chat route and llama.cpp server's OpenAI-compatible
/v1/chat/completions route.

### Ollama

On a supported computer with Ollama installed:

    ollama pull qwen2.5:1.5b

Start the Ollama service, then from the repository root run:

    python main.py ai-status
    python main.py ai-ask "Explain the project architecture"

### llama.cpp (including Termux)

The upstream llama.cpp documentation describes a native Termux build. Install
the build tools, clone llama.cpp, and build its server target:

    pkg update && pkg upgrade -y
    pkg install git cmake clang make -y
    git clone https://github.com/ggml-org/llama.cpp
    cd llama.cpp
    cmake -B build -DCMAKE_BUILD_TYPE=Release -DLLAMA_BUILD_SERVER=ON
    cmake --build build --target llama-server -j2

Run a compatible GGUF model (choose a quantization that fits available RAM):

    ./build/bin/llama-server -m ~/model.gguf --host 127.0.0.1 --port 8080 -c 2048

In another Termux session, configure OMEGA AI CORE:

    cd ~/HKA.1.1.1.1
    export OMEGA_AI_ENDPOINT=http://127.0.0.1:8080/v1/chat/completions
    export OMEGA_AI_MODEL=local-model
    python main.py ai-ask "Explain the project architecture"

Optional Ollama configuration:

    OMEGA_AI_ENDPOINT=http://127.0.0.1:11434/api/chat
    OMEGA_AI_MODEL=qwen2.5:1.5b

The initial model download requires internet. Once downloaded, inference can run
locally. Build time, model size and speed depend on device architecture, RAM,
thermal limits and available storage. Keep context size modest on phones.

The initial model download requires internet. Once downloaded, local inference can work offline.
Android/Termux support depends on device architecture, memory, storage and availability of a compatible local model runtime. A separate computer on the same network can host the model; configure the endpoint accordingly.

## Tests

Run the automated unit tests:

    python -m unittest discover -s tests -v

## Reports and local data

Reports are written to the selected output path. OMEGA AI conversation memory is stored at
`~/.omega_ai/memory.sqlite3`. Keep generated reports and local databases private when they contain sensitive information.
