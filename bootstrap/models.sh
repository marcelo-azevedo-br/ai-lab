#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RATE="10mbit"
DIRECT=0

MODELS=(
  "qwen2.5:7b"
  "llama3:8b"
  "deepseek-coder:6.7b"
  "phi3:mini"
)

usage() {
  cat <<'EOF'
Uso:
  sudo bash bootstrap/models.sh
  sudo bash bootstrap/models.sh --rate 5mbit
  bash bootstrap/models.sh --direct

Opcoes:
  --rate RATE   Limite de download por modelo. Padrao: 10mbit
  --direct      Faz `ollama pull` direto, sem limitador
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --rate)
      RATE="${2:-}"
      shift 2
      ;;
    --direct)
      DIRECT=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Opcao invalida: $1"
      usage
      exit 1
      ;;
  esac
done

if [[ "$DIRECT" -eq 0 && "${EUID}" -ne 0 ]]; then
  exec sudo bash "$SCRIPT_DIR/models.sh" --rate "$RATE"
fi

total="${#MODELS[@]}"
index=0

for model in "${MODELS[@]}"; do
  index=$((index + 1))
  started_at="$(date +%s)"

  echo
  echo "============================================================"
  echo "[$index/$total] Baixando $model"
  if [[ "$DIRECT" -eq 0 ]]; then
    echo "Limite ativo: $RATE"
    bash "$SCRIPT_DIR/pull_model_limited.sh" --rate "$RATE" "$model"
  else
    echo "Modo direto: sem limitador"
    ollama pull "$model"
  fi

  ended_at="$(date +%s)"
  elapsed=$((ended_at - started_at))
  minutes=$((elapsed / 60))
  seconds=$((elapsed % 60))
  echo "Concluido: $model em ${minutes}m${seconds}s"
done

echo "Modelos concluídos."
