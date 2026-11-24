"""Refresh the long-lived Threads token (extends 60 days) and print the new one
to a file for the workflow to store as the GitHub secret. Writes non-secret status
to threads/token_status.json."""
import json, os, sys, urllib.request, urllib.parse, urllib.error
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATUS = os.path.join(ROOT, "threads", "token_status.json")
tok = os.environ.get("THREADS_ACCESS_TOKEN", "").strip()
now = datetime.now(timezone.utc)
status = {"checked": now.isoformat()}
try:
    q = urllib.parse.urlencode({"grant_type": "th_refresh_token", "access_token": tok})
    with urllib.request.urlopen(f"https://graph.threads.net/refresh_access_token?{q}", timeout=60) as r:
        d = json.load(r)
    new = d["access_token"]
    exp = now + timedelta(seconds=int(d.get("expires_in", 0)))
    with open(os.environ["NEW_TOKEN_FILE"], "w") as f:
        f.write(new)
    status.update({"ok": True, "refreshed": now.isoformat(), "expires": exp.isoformat()})
    code = 0
except Exception as e:  # never print the token
    msg = e.read().decode(errors="replace") if isinstance(e, urllib.error.HTTPError) else str(e)
    status.update({"ok": False, "error": msg[:300].replace(tok, "***") if tok else msg[:300]})
    code = 1
old = {}
try:
    old = json.load(open(STATUS))
except Exception:
    pass
if not status["ok"] and old.get("expires"):
    status["expires"] = old["expires"]
json.dump(status, open(STATUS, "w"), indent=1)
print(json.dumps({k: v for k, v in status.items() if k != "error"}), status.get("error", ""))
sys.exit(code)
