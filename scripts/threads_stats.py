"""Pull Threads insights for every post we published and save aggregate numbers.

Writes threads/stats.json: per post id -> views, likes, replies, reposts, quotes, shares,
plus account-level followers. Only our own posts' counts; no other users' data.
Env: THREADS_ACCESS_TOKEN
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

API = "https://graph.threads.net/v1.0"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTED = os.path.join(ROOT, "threads", "posted.json")
POSTS = os.path.join(ROOT, "threads", "posts.json")
STATS = os.path.join(ROOT, "threads", "stats.json")
METRICS = "views,likes,replies,reposts,quotes,shares"


def get(path, params):
    url = f"{API}/{path}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{e.code}: {e.read().decode(errors='replace')}") from None


def values(resp):
    out = {}
    for m in resp.get("data", []):
        v = m.get("values") or [{}]
        out[m["name"]] = m.get("total_value", {}).get("value", v[-1].get("value", 0))
    return out


def main():
    token = os.environ.get("THREADS_ACCESS_TOKEN", "").strip()
    if not token:
        print("tiada token")
        return 0
    posted = json.load(open(POSTED, encoding="utf-8"))
    posts = {p["id"]: p for p in json.load(open(POSTS, encoding="utf-8"))}
    stats = {"updated": datetime.now(timezone.utc).isoformat(), "posts": {}}
    try:
        acc = values(get("me/threads_insights", {"metric": "followers_count", "access_token": token}))
        stats["followers"] = acc.get("followers_count")
    except RuntimeError as e:
        print("followers:", e)
    for pid, rec in posted.items():
        mid = rec.get("media_id")
        if rec.get("status") != "posted" or not mid:
            continue
        try:
            v = values(get(f"{mid}/insights", {"metric": METRICS, "access_token": token}))
        except RuntimeError as e:
            print(pid, e)
            continue
        p = posts.get(pid, {})
        v.update({"tag": p.get("topic_tag"), "text": p.get("text", "")[:80],
                  "series": bool(p.get("replies"))})
        stats["posts"][pid] = v
    with open(STATS, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=1, sort_keys=True)
    top = sorted(stats["posts"].items(), key=lambda kv: -(kv[1].get("views") or 0))[:5]
    for pid, v in top:
        print(pid, v.get("views"), v.get("tag"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
