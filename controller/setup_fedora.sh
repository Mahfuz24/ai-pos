#!/usr/bin/env bash
# Fedora local-only setup. Does not deploy or authorize release.
set -euo pipefail
umask 077
command -v python3 >/dev/null || { echo "Python 3 required"; exit 1; }
command -v git >/dev/null || { echo "Git required"; exit 1; }
base="${XDG_STATE_HOME:-$HOME/.local/state}/ai-pos-controller"
mkdir -p "$base"
chmod 700 "$base"
db="$base/redeemed.sqlite3"
python3 - "$db" <<'PY'
import sqlite3, sys, os
p = sys.argv[1]
conn = sqlite3.connect(p)
conn.execute("CREATE TABLE IF NOT EXISTS approvals (nonce TEXT PRIMARY KEY, sha TEXT NOT NULL)")
conn.commit()
conn.close()
os.chmod(p, 0o600)
print("Replay database initialized:", p)
PY
printf '\nController setup initialized.\n'
printf 'Set AI_POS_REPLAY_DB=%s\n' "$db"
printf 'Keep Founder key outside repo and never paste it into ChatGPT.\n'
printf 'GITHUB_TOKEN must be a read-only token if used; public Actions metadata can be read without credentials but current controller requires a token.\n'
printf 'No approval, merge, or deployment performed.\n'
