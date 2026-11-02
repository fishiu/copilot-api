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

- 2026-11-02: deployment line remains on reviewed v2.8.2. Upstream `dev` was discovered at v2.8.6 (`32768e2`); its integration and deployment acceptance are tracked separately. The optional local error-detail/image-preview patches are not part of this deployment line.
