#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Uso:
  sudo bash bootstrap/pull_model_limited.sh --rate 20mbit qwen2.5:7b

Opcoes:
  --rate RATE   Limite total de banda do WSL durante o pull. Ex.: 10mbit, 20mbit, 5000kbit
  --iface IFACE Interface de rede do WSL. Se omitido, o script tenta detectar automaticamente.

Observacoes:
  - O limite vale para o trafego de saida do WSL durante a execucao do comando.
  - Ao final, a regra e removida automaticamente.
  - Requer sudo por causa do tc.
EOF
}

RATE=""
IFACE=""
MODEL=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --rate)
      RATE="${2:-}"
      shift 2
      ;;
    --iface)
      IFACE="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      MODEL="$1"
      shift
      ;;
  esac
done

if [[ -z "$RATE" || -z "$MODEL" ]]; then
  usage
  exit 1
fi

if [[ "${EUID}" -ne 0 ]]; then
  echo "Este script precisa de sudo."
  exit 1
fi

if [[ -z "$IFACE" ]]; then
  IFACE="$(awk '$2 == "00000000" { print $1; exit }' /proc/net/route)"
fi

if [[ -z "$IFACE" ]]; then
  echo "Nao foi possivel detectar a interface padrao do WSL. Use --iface."
  exit 1
fi

cleanup() {
  tc qdisc del dev "$IFACE" root >/dev/null 2>&1 || true
}

trap cleanup EXIT

echo "Aplicando limite de banda no WSL"
echo "interface: $IFACE"
echo "rate: $RATE"
echo "model: $MODEL"

tc qdisc del dev "$IFACE" root >/dev/null 2>&1 || true
tc qdisc add dev "$IFACE" root tbf rate "$RATE" burst 256kbit latency 400ms

echo "Iniciando ollama pull com limite"
ollama pull "$MODEL"

echo "Pull concluido e limite removido."
