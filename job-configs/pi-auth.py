"""Print the Pi login for the verifier's real.* family, as CODECLIMB_BENCH_PI_AUTH expects it: an auth.json holding one
entry. Capture it, never display it:

    export CODECLIMB_BENCH_PI_AUTH="$(python3 job-configs/pi-auth.py)"            # the operator's Copilot login
    export CODECLIMB_BENCH_PI_AUTH="$(python3 job-configs/pi-auth.py anthropic)"  # an Anthropic API key

`anthropic` takes ANTHROPIC_API_KEY from the environment, else from the repo's .env. The verifier then runs the real
tier's Haiku models through the Claude API (verifier/families.py, ANTHROPIC_IDS). The key reaches the verifier only;
the harness runs on the subscription and never gets it.
"""

import json
import os
import sys
from pathlib import Path

if sys.argv[1:] == ["anthropic"]:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    env = Path(__file__).resolve().parents[1] / ".env"
    if not key and env.exists():
        for line in env.read_text().splitlines():
            if line.startswith("ANTHROPIC_API_KEY="):
                key = line.partition("=")[2].strip().strip("'\"")
    if not key:
        sys.exit("no ANTHROPIC_API_KEY in the environment or .env")
    print(json.dumps({"anthropic": {"type": "api_key", "key": key}}))
    sys.exit(0)

path = os.environ.get("CODECLIMB_PI_AUTH_PATH") or os.path.expanduser("~/.pi/agent/auth.json")
entry = json.load(open(path)).get("github-copilot")
if not entry:
    sys.exit(f"{path}: no github-copilot login; run `npx pi`, then `/login github-copilot`")
print(json.dumps({"github-copilot": entry}))
