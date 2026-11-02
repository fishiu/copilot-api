"""Prepare the paused macOS experiment; starting it requires --start."""
import argparse
import json
import os
import pathlib
import plistlib
import shutil
import subprocess
import sys

if sys.platform != "darwin":
    raise SystemExit("This installer is for macOS launchd only")
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--port", type=int, default=4143)
parser.add_argument("--base", type=pathlib.Path,
                    default=pathlib.Path.home() / ".local/share/capi-v2-plaintext-test")
parser.add_argument("--bun", type=pathlib.Path,
                    default=pathlib.Path(shutil.which("bun") or "bun"))
parser.add_argument("--start", action="store_true", help="Explicitly start this experiment once")
parser.add_argument("--replace-definition", action="store_true",
                    help="Replace an inspected, unloaded experiment definition")
args = parser.parse_args()
if args.port in (4141, 4142) or not 1 <= args.port <= 65535:
    parser.error("Use an experiment port, not production 4141/4142")
home = pathlib.Path.home()
base = args.base.expanduser().resolve()
label = "com.fishiu.capi.codex-plaintext-v2"
target = home / "Library/LaunchAgents" / (label + ".plist")
entry = base / "runtime/dist/main.js"
bun = args.bun.expanduser().resolve()
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
    "ProgramArguments": [str(bun), str(entry), "--api-home=" + str(base / "data"), "start", "--host", "127.0.0.1", "--port", str(args.port)],
    "WorkingDirectory": str(base / "data"),
    "RunAtLoad": False,
    "KeepAlive": False,
    "EnvironmentVariables": {
        "HOME": str(home), "NODE_ENV": "production", "NODE_USE_SYSTEM_CA": "1", "NO_COLOR": "1",
        "CAPI_PLAINTEXT_V2_MODELS": "gpt-6-astra,gpt-6.1-sol",
        "CAPI_ALPHA_SEARCH_FORWARD_BASE": "http://127.0.0.1:4142",
        "CAPI_ALPHA_SEARCH_FORWARD_API_HOME": str(home / ".local/share/copilot-api-codex-2"),
    },
    "StandardOutPath": str(logs / "gateway.log"),
    "StandardErrorPath": str(logs / "gateway.log"),
}
if target.exists() and plistlib.loads(target.read_bytes()) != plist and not args.replace_definition:
    raise SystemExit("Existing service definition differs; inspect it, then use --replace-definition")
target.write_bytes(plistlib.dumps(plist))
subprocess.run(["plutil", "-lint", str(target)], check=True)
if args.start:
    subprocess.run(["launchctl", "bootstrap", f"gui/{os.getuid()}", str(target)], check=True)
    subprocess.run(["launchctl", "kickstart", service], check=True)
print(json.dumps({"label": label, "plist": str(target), "port": args.port,
                  "loaded": args.start, "autostart": False}))
