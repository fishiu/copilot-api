#!/bin/sh
# Private test instance only; never installs a daemon or restarts production.
set -eu
lab_base="${CAPI_LAB_BASE:-$HOME/.local/share/capi-v2-plaintext-test}"
lab_port="${CAPI_LAB_PORT:-4143}"
case "$lab_port" in
  4141|4142) echo 'Refusing to use a production gateway port for the lab' >&2; exit 1 ;;
esac
export CAPI_PLAINTEXT_V2_MODELS='gpt-6-astra,gpt-6.1-sol'
export NODE_USE_SYSTEM_CA=1
export CAPI_ALPHA_SEARCH_FORWARD_BASE="http://127.0.0.1:4142"
export CAPI_ALPHA_SEARCH_FORWARD_API_HOME="$HOME/.local/share/copilot-api-codex-2"
lab_bun="${CAPI_LAB_BUN:-bun}"
exec "$lab_bun" "$lab_base/runtime/dist/main.js" --api-home="$lab_base/data" start --host 127.0.0.1 --port "$lab_port"
