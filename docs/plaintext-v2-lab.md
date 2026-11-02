# Paused plaintext V2 lab

This experimental branch adds an exact-model, opt-in adapter at the native Copilot Responses boundary. It retains the official Codex V2 scheduler while requesting readable collaboration messages under a nonreserved namespace and restoring `collaboration` with `encrypted_function_args: []` for the three message tools.

The default empty `CAPI_PLAINTEXT_V2_MODELS` disables adaptation. Unknown encrypted agent messages and recognizable opaque historical message arguments are rejected, rather than discarded or relabeled. User text, argument bytes, call IDs, unrelated tools, reasoning and compaction content are preserved. The lab uses HTTP Responses only; no WebSocket acceptance is claimed. This is a new-history experiment, not a legacy-history repair.

## Local layout

- Source: this isolated Git worktree, based on official CAPI v2.8.2 (`a500447`).
- Runtime and private data: `$HOME/.local/share/capi-v2-plaintext-test/`.
- Codex config, catalog and sessions: `$HOME/.codex-v2-test/`.
- Listener: `127.0.0.1:4143`; reserved for manual experiments and stopped by default. The former 60444 listener is retired.
- Synthetic fixtures and full test logs stay outside Git, under the private data directory.

The test gateway has its own API/admin keys, configuration, SQLite data and a private copy of the existing GitHub credential. It uses the same upstream account. It does not share the production database, copy Codex OAuth refresh credentials or restart production services.

## Build and run

The maintained fork now builds from source using a frozen lockfile. See [fork maintenance](fork-maintenance.md) for the deployment and upstream-integration branches. The lab retains its independent runtime, data and Codex home; developing the formal gateway does not authorize replacing an experiment in progress.

`scripts/build-plaintext-lab.ts` remains a fallback for reproducing the original experiment. It compiles the same dependency-free adapter used in the source handler, copies an official 2.8.2 runtime to a separate output directory, and applies checked, unique integration anchors to that copy. Any mismatching anchor aborts. Such output must be labeled an official-runtime overlay, not a full source build.

```sh
bun scripts/build-plaintext-lab.ts /path/to/official-2.8.2-runtime "$HOME/.local/share/capi-v2-plaintext-test/runtime"
scripts/start-plaintext-lab.sh
```

In another terminal:

```sh
CODEX_HOME="$HOME/.codex-v2-test" codex --no-daemon
```

The initial private configuration must already exist. The start script never obtains credentials interactively or edits production configuration.

## Validation

```sh
bun test --coverage tests/plaintext-v2.test.ts tests/plaintext-v2-alpha-forward.test.ts > /tmp/plaintext-v2-test.log 2>&1
python3 scripts/probe-plaintext-v2.py
python3 scripts/compact-plaintext-lab.py
```

The probe refuses to overwrite an existing acceptance receipt. Review existing results before repeating. The CSV audit uses synthetic deterministic data, two real model workers, explicit progress messages and recall by the original children. The compact probe is meant to run after restarting the private gateway. It matches the parent's thread ID when awaiting completion, so a child's completion cannot be mistaken for the parent's.

Tests do not establish overnight reliability, broad model compatibility, full command auto-review or production readiness. An additional Guardian-shaped synthetic request verifies readable task context survives the existing normalization path; it is not a full approval-flow test. Failed requests and test-harness mistakes remain in the private evidence and usage totals.

## Explicitly starting the paused experiment

The 2026-10-30 experiment was temporarily the local default on port 60444. On 2026-11-02 the adapter was selected for promotion into the maintained formal gateway, and this separate experiment was reserved on port 4143. Existing private evidence remains unchanged.

`scripts/install-plaintext-service.py` prepares `com.fishiu.capi.codex-plaintext-v2` with `RunAtLoad=false` and `KeepAlive=false`. Its default action only writes the definition. `--start` explicitly loads and starts it once. It refuses to overwrite a loaded service or a differing definition without inspection; after unloading, `--replace-definition` allows the inspected port migration. Production ports 4141 and 4142 are rejected.

```sh
python3 scripts/install-plaintext-service.py --port 4143 --bun /path/to/validated/bun
# Or run in the foreground; Ctrl-C stops only this experiment:
CAPI_LAB_BUN=/path/to/validated/bun scripts/start-plaintext-lab.sh
```

`CAPI_LAB_PORT`, `CAPI_LAB_BASE`, `CODEX_LAB_HOME`, `CAPI_KEY_HELPER` and `CODEX_LAB_EXECUTABLE` parameterize acceptance without copying another machine's paths. Default probes use 4143 and the existing independent data. They do not overwrite the original acceptance receipt automatically.

The default Codex config retains existing permissions, MCP, plugins and model choice. Only Astra and 6.1 Sol advertise V2 in a separate catalog; the other models and legacy selectable profiles retain V1.

The new instance keeps GitHub credentials separate but does not duplicate the original gateway's refreshing Codex OAuth credentials. Optional `CAPI_ALPHA_SEARCH_FORWARD_BASE` plus `CAPI_ALPHA_SEARCH_FORWARD_API_HOME` preserves native alpha search through the existing local gateway. Forwarding is restricted to loopback HTTP, replaces inbound authentication with the upstream gateway's private API key, and preserves body and query data. The old search gateway is therefore a live dependency, not an unused process.

Tests cover credential replacement, disabled/partial configuration, remote-target rejection, exact request forwarding and missing-key errors. Native image search and the real default Codex parent/child route are checked after service deployment. Existing already-loaded Codex sessions are not forcibly reconfigured or restarted.
