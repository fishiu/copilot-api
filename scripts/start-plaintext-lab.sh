#!/bin/sh
# Private test instance only; never installs a daemon or restarts production.
set -eu
lab_base="$HOME/.local/share/capi-v2-plaintext-test"
export CAPI_PLAINTEXT_V2_MODELS='gpt-6-astra,gpt-6.1-sol'
export NODE_USE_SYSTEM_CA=1
export CAPI_ALPHA_SEARCH_FORWARD_BASE="http://127.0.0.1:4142"
export CAPI_ALPHA_SEARCH_FORWARD_API_HOME="$HOME/.local/share/copilot-api-codex-2"
exec "$HOME/.local/share/capi-runtimes/bun-1.4.4/bun" "$lab_base/runtime/dist/main.js" --api-home="$lab_base/data" start --host 127.0.0.1 --port 60444
