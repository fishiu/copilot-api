"""Install the already-validated local plaintext CAPI as a per-user launchd service."""
import json
import os
import pathlib
import plistlib
import subprocess
import sys

if sys.platform != "darwin":
    raise SystemExit("This installer is for macOS launchd only")
home = pathlib.Path.home()
base = home / ".local/share/capi-v2-plaintext-test"
label = "com.fishiu.capi.codex-plaintext-v2"
target = home / "Library/LaunchAgents" / (label + ".plist")
entry = base / "runtime/dist/main.js"
bun = home / ".local/share/capi-runtimes/bun-1.4.4/bun"
for path in [entry, bun, base / "data/config.json"]:
    if not path.is_file():
        raise SystemExit("Missing validated runtime or private data: " + str(path))
service = f"gui/{os.getuid()}/{label}"
if subprocess.run(["launchctl", "print", service], capture_output=True).returncode == 0:
    raise SystemExit("Service is already loaded; inspect before replacing a running instance")
logs = base / "data/logs"
logs.mkdir(exist_ok=True)
plist = {
    "Label": label,
    "ProgramArguments": [str(bun), str(entry), "--api-home=" + str(base / "data"), "start", "--host", "127.0.0.1", "--port", "60444"],
    "WorkingDirectory": str(base / "data"),
    "RunAtLoad": True,
    "KeepAlive": True,
    "ThrottleInterval": 10,
    "EnvironmentVariables": {
        "HOME": str(home), "NODE_ENV": "production", "NODE_USE_SYSTEM_CA": "1", "NO_COLOR": "1",
        "CAPI_PLAINTEXT_V2_MODELS": "gpt-6-astra,gpt-6.1-sol",
        "CAPI_ALPHA_SEARCH_FORWARD_BASE": "http://127.0.0.1:4142",
        "CAPI_ALPHA_SEARCH_FORWARD_API_HOME": str(home / ".local/share/copilot-api-codex-2"),
    },
    "StandardOutPath": str(logs / "gateway.log"),
    "StandardErrorPath": str(logs / "gateway.log"),
}
if target.exists() and plistlib.loads(target.read_bytes()) != plist:
    raise SystemExit("Existing service definition differs; inspect it before replacement")
target.write_bytes(plistlib.dumps(plist))
subprocess.run(["plutil", "-lint", str(target)], check=True)
subprocess.run(["launchctl", "bootstrap", f"gui/{os.getuid()}", str(target)], check=True)
print(json.dumps({"label": label, "plist": str(target), "port": 60444, "loaded": True}))
