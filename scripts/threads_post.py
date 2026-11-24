"""Post scheduled Threads posts for @tmxlab.

Reads threads/posts.json, posts anything that is due (and not posted yet)
through the official Threads API, then records it in threads/posted.json.

Env:
  THREADS_ACCESS_TOKEN  long-lived Threads user token (GitHub secret)
  MODE                  "post" (default) | "check" (only verify the token)
  DRY_RUN               "1" to print what would be posted without posting
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

API = "https://graph.threads.net/v1.0"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(ROOT, "threads", "posts.json")
POSTED = os.path.join(ROOT, "threads", "posted.json")

# A post is only sent if we are at most this late (GitHub cron can lag).
# Older missed posts are skipped so we never dump a backlog at once.
LATE_WINDOW = timedelta(hours=3)
MAX_PER_RUN = 1


def call(method, path, params):
    data = urllib.parse.urlencode(params).encode()
    url = f"{API}/{path}"
    if method == "GET":
        req = urllib.request.Request(f"{url}?{data.decode()}")
    else:
        req = urllib.request.Request(url, data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"Threads API {e.code}: {body}") from None


def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def main():
    token = os.environ.get("THREADS_ACCESS_TOKEN", "").strip()
    if not token:
        print("THREADS_ACCESS_TOKEN belum diset.")
        return 1 if os.environ.get("MODE") == "check" else 0

    # Always verify the token first so a bad/expired token fails the run (visible in Actions).
    me = call("GET", "me", {"fields": "id,username", "access_token": token})
    print(f"Token OK. Akaun: @{me.get('username')}")
    if os.environ.get("MODE") == "check":
        return 0

    dry = os.environ.get("DRY_RUN") == "1"
    posts = load(POSTS, [])
    posted = load(POSTED, {})
    now = datetime.now(timezone.utc)

    due = []
    for p in posts:
        if p["id"] in posted:
            continue
        t = datetime.fromisoformat(p["time"])
        if t > now:
            continue
        if now - t > LATE_WINDOW:
            posted[p["id"]] = {"status": "skipped_late", "at": now.isoformat()}
            print(f"skip (lambat): {p['id']}")
            continue
        due.append(p)

    sent = 0
    for p in due[:MAX_PER_RUN]:
        print(f"post: {p['id']} :: {p['text'][:60]!r}")
        if dry:
            continue
        params = {"media_type": "TEXT", "text": p["text"], "access_token": token}
        tag = (p.get("topic_tag") or "").replace(".", "").replace("&", "").strip()[:50]
        if tag:
            params["topic_tag"] = tag  # community/topic tag (one per post)
        c = call("POST", "me/threads", params)
        time.sleep(5)
        r = call("POST", "me/threads_publish",
                 {"creation_id": c["id"], "access_token": token})
        root = r.get("id")
        rec = {"status": "posted", "media_id": root, "replies": [],
               "at": datetime.now(timezone.utc).isoformat()}
        # Optional reply chain: each reply goes under the previous one, in order.
        parent = root
        for txt in p.get("replies", []):
            time.sleep(10)
            rc = call("POST", "me/threads", {"media_type": "TEXT", "text": txt,
                                              "reply_to_id": parent, "access_token": token})
            time.sleep(5)
            rr = call("POST", "me/threads_publish",
                      {"creation_id": rc["id"], "access_token": token})
            parent = rr.get("id")
            rec["replies"].append(parent)
        if not rec["replies"]:
            rec.pop("replies")
        posted[p["id"]] = rec
        sent += 1

    if not dry:
        with open(POSTED, "w", encoding="utf-8") as f:
            json.dump(posted, f, ensure_ascii=False, indent=1, sort_keys=True)
    print(f"siap. dihantar: {sent}, menunggu: {len(due) - sent}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
