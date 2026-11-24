"""Comment handling for @tmxlab.

1. outbox: send replies listed in threads/outbox.json that are not sent yet
   item: {"reply_to_id": "<comment id>", "text": "..."}
2. inbox: collect new comments from other people on our recent posts into
   threads/inbox.json (only comment id, text, context; no usernames stored)

Env: THREADS_ACCESS_TOKEN
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

API = "https://graph.threads.net/v1.0"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "threads")
POSTED, POSTS = os.path.join(D, "posted.json"), os.path.join(D, "posts.json")
INBOX, OUTBOX, SENT = (os.path.join(D, f) for f in ("inbox.json", "outbox.json", "outbox_sent.json"))
LOOKBACK = timedelta(days=10)


def call(method, path, params):
    q = urllib.parse.urlencode(params)
    req = (urllib.request.Request(f"{API}/{path}?{q}") if method == "GET"
           else urllib.request.Request(f"{API}/{path}", data=q.encode(), method="POST"))
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{e.code}: {e.read().decode(errors='replace')}") from None


def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, sort_keys=True)


def send_outbox(token, me):
    out, sent = load(OUTBOX, []), load(SENT, {})
    for item in out:
        rid, txt = item.get("reply_to_id"), (item.get("text") or "").strip()
        if not rid or not txt or rid in sent:
            continue
        c = call("POST", "me/threads", {"media_type": "TEXT", "text": txt,
                                         "reply_to_id": rid, "access_token": token})
        time.sleep(5)
        r = call("POST", "me/threads_publish", {"creation_id": c["id"], "access_token": token})
        sent[rid] = {"reply_id": r.get("id"), "at": datetime.now(timezone.utc).isoformat()}
        print("balas:", rid)
        time.sleep(5)
    save(SENT, sent)
    return sent


def fetch_inbox(token, me, sent):
    posted = load(POSTED, {})
    texts = {p["id"]: p["text"] for p in load(POSTS, [])}
    inbox = {c["id"]: c for c in load(INBOX, [])}
    now = datetime.now(timezone.utc)
    for pid, rec in posted.items():
        mid = rec.get("media_id")
        at = rec.get("at")
        if not mid or not at or now - datetime.fromisoformat(at) > LOOKBACK:
            continue
        try:
            conv = call("GET", f"{mid}/conversation", {
                "fields": "id,text,username,timestamp,replied_to",
                "reverse": "false", "access_token": token}).get("data", [])
        except RuntimeError as e:
            print(pid, e)
            continue
        ours = {c["id"]: c.get("text", "") for c in conv if c.get("username") == me}
        ours[mid] = texts.get(pid, "")
        for c in conv:
            if c.get("username") == me or not c.get("text"):
                continue
            parent = (c.get("replied_to") or {}).get("id")
            item = inbox.get(c["id"], {})
            item.update({"id": c["id"], "post": pid, "post_text": texts.get(pid, "")[:300],
                         "parent_is_ours": parent in ours,
                         "parent_text": ours.get(parent, "")[:300],
                         "text": c["text"], "timestamp": c.get("timestamp"),
                         "answered": c["id"] in sent
                         or any(x.get("replied_to", {}).get("id") == c["id"]
                                for x in conv if x.get("username") == me)})
            inbox[c["id"]] = item
    items = sorted(inbox.values(), key=lambda x: x.get("timestamp") or "")
    save(INBOX, items)
    print("komen belum balas:", sum(1 for x in items if not x["answered"]))


def main():
    token = os.environ.get("THREADS_ACCESS_TOKEN", "").strip()
    if not token:
        print("tiada token")
        return 0
    me = call("GET", "me", {"fields": "username", "access_token": token}).get("username")
    sent = send_outbox(token, me)
    fetch_inbox(token, me, sent)
    return 0


if __name__ == "__main__":
    sys.exit(main())
