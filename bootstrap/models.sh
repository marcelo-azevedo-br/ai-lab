#!/usr/bin/env bash
set -euo pipefail

MODELS=(
  "qwen2.5:7b"
  "llama3:8b"
  "deepseek-coder:6.7b"
  "phi3:mini"
)

for model in "${MODELS[@]}"; do
  echo "==> Baixando $model"
  ollama pull "$model"
done

echo "Modelos concluídos."
