#!/usr/bin/env bash
set -euo pipefail

echo "==> Binarios"
for cmd in python3 git codex ollama; do
  command -v "$cmd" >/dev/null 2>&1 && echo "ok: $cmd" || echo "missing: $cmd"
done

echo "==> Codex"
codex --version || true

echo "==> Ollama"
ollama --version || true

echo "==> Modelos"
ollama list || true
