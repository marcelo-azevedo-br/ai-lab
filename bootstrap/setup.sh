#!/usr/bin/env bash
set -euo pipefail

echo "==> Verificando binarios"
for cmd in python3 git node npm codex ollama; do
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "ok: $cmd -> $(command -v "$cmd")"
  else
    echo "missing: $cmd"
  fi
done

echo "==> Estrutura esperada"
mkdir -p bootstrap config docs factory/agents factory/prompts factory/runs products src tests
echo "estrutura pronta"

echo "==> Proximos passos"
echo "1. Rode bootstrap/models.sh para baixar os modelos do Ollama"
echo "2. Rode bootstrap/check.sh para validar o stack"
echo "3. Execute python3 run_factory.py check"
