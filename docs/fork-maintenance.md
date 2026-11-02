# Maintained plaintext V2 fork

Development and release of the plaintext V2 adapter live in [fishiu/copilot-api](https://github.com/fishiu/copilot-api). The original project remains [caozhiyuan/copilot-api](https://github.com/caozhiyuan/copilot-api). No upstream pull request is authorized until the owner explicitly requests one.

## Branches and remotes

- `fishiu/plaintext-v2`: deployable source based on reviewed upstream v2.8.2 (`a500447`), plus the previously accepted plaintext adapter and paused lab tooling.
- `fishiu/plaintext-v2-upstream`: development integration branch that merges upstream `dev`; a merge or passing unit test does not promote its new upstream version to production.
- `upstream`: `https://github.com/caozhiyuan/copilot-api.git`, fetch and merge source.
- `fork`: `https://github.com/fishiu/copilot-api.git`, publish maintained branches. Existing shared worktrees may retain their original `origin`; do not silently repoint them.

The fork's pre-existing `dev` branch is preserved. Use `git merge`, not a destructive mirror or force push, when following upstream. Fetch current upstream, inspect changes since the last merged commit (including auth, transport, tool metadata, search and defaults), merge into the integration branch, resolve conflicts explicitly and rerun affected checks. Update the integration record below after each accepted merge. Promote a reviewed commit to the deployment branch only after the actual runtime and required capabilities are verified. Preserve unrelated local patches and retain a tested rollback runtime.

## Source build

```sh
git switch fishiu/plaintext-v2
bun install --frozen-lockfile --ignore-scripts
bun run build
# Fully bundle dependencies for a separately deployed runtime:
bun run build:desktop
```

Use the reviewed Bun executable on each machine. `build` leaves normal package dependencies external; `build:desktop` uses the project's existing bundle-all configuration and does not launch Electron. Copy that build's `dist/`, `pages/` and module `package.json` into a separate immutable deployment directory; record the source commit, lockfile hash, Bun version and runtime artifact hashes in its private deployment manifest. A source build and an official bundle with local overlay are distinct distributions and must be reported separately. Never deploy from a worktree while a build or merge can overwrite a running process's modules.

## Deployment contract

Keep the formal gateway's port, API home, keys, OAuth ownership, proxy, bind address and service manager. Enable the adapter with `CAPI_PLAINTEXT_V2_MODELS=gpt-6-astra,gpt-6.1-sol`. New Codex sessions using the adapted HTTP Responses route advertise V2 for those exact two models; other models retain their current policy. Disable client Responses WebSocket support for this route. Keep independent remote compaction settings and the native search path.

Production gateways with native OAuth search use their existing credentials directly. The optional loopback alpha-search forwarding module is only for an isolated gateway without refresh-token ownership; do not point a gateway at itself. Disable forwarding in the formal native-search owner.

Do not silently decrypt, remove or relabel historical opaque collaboration content. Existing encrypted agent histories stay fail-closed. A plaintext child must return `input_text`, with message tools carrying `encrypted_function_args=[]`; an ordinary model answer is insufficient evidence of this contract. Verify both streaming and nonstreaming translation, same-child follow-up, and the affected runtime route. Existing sessions are not force-restarted or rewritten.

The independent experiment is reserved at `127.0.0.1:4143`, stopped by default. Its data and original evidence remain available; see [lab operations](plaintext-v2-lab.md).

## Rollback and removal

Before replacing a formal runtime, retain its service definition and private rollback pointer. If readable messages are misclassified, aliases leak, native search regresses or resumption fails, preserve a sanitized receipt and select the known-good runtime/V1 profile. Unsetting the environment switch disables adaptation for new traffic; it does not convert an existing plaintext history back to an encrypted one.

Remove this compatibility adapter only after the owner accepts an upstream or official replacement and fresh parent/child, follow-up, compaction, process restart, and search checks establish the replacement's behavior. A later model catalog claiming V2 support is not sufficient.

## Integration record

- 2026-11-02: deployment line remains on reviewed v2.8.2 at `cb18442498aa96434b04f2c4620aac05886cfdfb`; its two adapter helpers have 100% line/function coverage, Responses/alpha-search affected tests pass (111 tests), and TypeScript plus both source build modes pass with Bun 1.4.4. The optional local error-detail/image-preview patches are not included.
- 2026-11-02: merged upstream `dev` v2.8.6 (`32768e26136169099e7063125045f565130517ee`) without conflict in merge `7d8b4f53c8c781f32fc2c82f33216f10dd907042`. Upstream introduces `codexMultiAgentV1` (default false); enabling it changes model metadata and must not silently override the plaintext V2 policy.
- 2026-11-02: completed development validation of that v2.8.6 merge. The configured registry initially returned 404 for `stream-json@3.8.0` and `stream-chain@4.4.1`, and the local official-registry connection closed. Exact official tarballs were retrieved through a working network, checked against both lockfile SHA-512 digests, and extracted only into this development worktree's `node_modules`. `bun install --offline --frozen-lockfile --ignore-scripts` then checked 400 installs across 442 packages without changes; no dependency version, lockfile or global registry configuration was altered. Full gateway TypeScript check, normal source build (36 files, 2.92 MB), dependency-bundled source build (68 files, 24.75 MB), and targeted lint passed with Bun 1.4.4. The bundled CLI also ran from an isolated directory without `node_modules`. Affected regression tests passed: 880 tests across 16 files, zero failures; both plaintext helpers have 100% function/line coverage and the new streaming JSON helper has 83.33% function/100% line coverage. This validates the development gateway package, not the Electron application or live parent/child/search deployment; the accepted 2.8.2 deployment commit remains unchanged.
