#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Uso:
  sudo bash bootstrap/pull_model_limited.sh --rate 10mbit qwen2.5:7b

Opcoes:
  --rate RATE   Limite de download no WSL. Ex.: 10mbit, 20mbit, 5000kbit
  --iface IFACE Interface de rede principal do WSL. Se omitido, o script tenta detectar.
  --ifb IFB     Interface IFB para shaping de entrada. Padrao: ifb0

Observacoes:
  - Este script limita trafego de entrada, que e o que importa para `ollama pull`.
  - Requer sudo e suporte a `ifb`.
  - Ao final, remove as regras automaticamente.
EOF
}

RATE=""
IFACE=""
IFB_DEV="ifb0"
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
    --ifb)
      IFB_DEV="${2:-}"
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

if ! command -v tc >/dev/null 2>&1; then
  echo "tc nao encontrado."
  exit 1
fi

if ! command -v modprobe >/dev/null 2>&1; then
  echo "modprobe nao encontrado."
  exit 1
fi

cleanup() {
  tc qdisc del dev "$IFACE" ingress >/dev/null 2>&1 || true
  tc qdisc del dev "$IFB_DEV" root >/dev/null 2>&1 || true
  ip link set dev "$IFB_DEV" down >/dev/null 2>&1 || true
}

trap cleanup EXIT

echo "Carregando IFB"
modprobe ifb numifbs=1

if ! ip link show "$IFB_DEV" >/dev/null 2>&1; then
  ip link add "$IFB_DEV" type ifb
fi
ip link set dev "$IFB_DEV" up

echo "Aplicando limite de download no WSL"
echo "iface: $IFACE"
echo "ifb: $IFB_DEV"
echo "rate: $RATE"
echo "model: $MODEL"

tc qdisc del dev "$IFACE" ingress >/dev/null 2>&1 || true
tc qdisc del dev "$IFB_DEV" root >/dev/null 2>&1 || true

tc qdisc add dev "$IFACE" ingress
tc filter add dev "$IFACE" parent ffff: protocol all u32 match u32 0 0 action mirred egress redirect dev "$IFB_DEV"
tc qdisc add dev "$IFB_DEV" root tbf rate "$RATE" burst 256kbit latency 400ms

echo "Iniciando ollama pull com limite de download"
ollama pull "$MODEL"

echo "Pull concluido e limite removido."
