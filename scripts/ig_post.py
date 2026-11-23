"""Post scheduled Instagram posts for @tmxlab (Instagram API with Instagram Login).

Reads instagram/posts.json, publishes anything due, records in instagram/posted.json.
Item: {"id", "time", "type": "IMAGE"|"CAROUSEL"|"REELS", "caption", "media": [urls]}
Images must be public JPEG URLs; reels a public MP4 URL.

Env: IG_ACCESS_TOKEN, MODE ("post" | "check"), DRY_RUN ("1")
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

API = "https://graph.instagram.com/v21.0"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS = os.path.join(ROOT, "instagram", "posts.json")
POSTED = os.path.join(ROOT, "instagram", "posted.json")
LATE_WINDOW = timedelta(hours=2)


def call(method, path, params):
    data = urllib.parse.urlencode(params).encode()
    url = f"{API}/{path}"
    req = (urllib.request.Request(f"{url}?{data.decode()}") if method == "GET"
           else urllib.request.Request(url, data=data, method="POST"))
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Instagram API {e.code}: {e.read().decode(errors='replace')}") from None


def wait_ready(cid, token, tries=30, delay=10):
    for _ in range(tries):
        s = call("GET", cid, {"fields": "status_code", "access_token": token}).get("status_code")
        if s == "FINISHED":
            return
        if s in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"container {cid} status {s}")
        time.sleep(delay)
    raise RuntimeError(f"container {cid} not ready")


def publish(uid, p, token):
    t, media, cap = p.get("type", "IMAGE"), p["media"], p.get("caption", "")
    if t == "CAROUSEL":
        kids = []
        for u in media[:10]:
            c = call("POST", f"{uid}/media", {"image_url": u, "is_carousel_item": "true",
                                               "access_token": token})
            kids.append(c["id"])
        for k in kids:
            wait_ready(k, token)
        cid = call("POST", f"{uid}/media", {"media_type": "CAROUSEL", "children": ",".join(kids),
                                             "caption": cap, "access_token": token})["id"]
    elif t == "REELS":
        cid = call("POST", f"{uid}/media", {"media_type": "REELS", "video_url": media[0],
                                             "caption": cap, "access_token": token})["id"]
    else:
        cid = call("POST", f"{uid}/media", {"image_url": media[0], "caption": cap,
                                             "access_token": token})["id"]
    wait_ready(cid, token)
    return call("POST", f"{uid}/media_publish", {"creation_id": cid, "access_token": token}).get("id")


def load(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default


def main():
    token = os.environ.get("IG_ACCESS_TOKEN", "").strip()
    mode = os.environ.get("MODE", "post")
    if not token:
        print("IG_ACCESS_TOKEN belum diset.")
        return 1 if mode == "check" else 0  # "setup" mode: belum ada token, jangan gagal

    me = call("GET", "me", {"fields": "user_id,username", "access_token": token})
    uid = me.get("user_id") or me.get("id")
    print(f"Token OK. Akaun: @{me.get('username')}")
    if mode in ("check", "setup"):
        return 0

    dry = os.environ.get("DRY_RUN") == "1"
    posts, posted = load(POSTS, []), load(POSTED, {})
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

    for p in due[:1]:
        print(f"post: {p['id']} ({p.get('type')}, {len(p['media'])} media)")
        if dry:
            continue
        mid = publish(uid, p, token)
        posted[p["id"]] = {"status": "posted", "media_id": mid,
                           "at": datetime.now(timezone.utc).isoformat()}

    if not dry:
        with open(POSTED, "w", encoding="utf-8") as f:
            json.dump(posted, f, ensure_ascii=False, indent=1, sort_keys=True)
    print("siap.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
