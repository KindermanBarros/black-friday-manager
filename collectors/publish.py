"""Append-only GitHub Contents publication, including failure snapshots; stdlib only."""
import base64
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

FEEDS = {"collector-00", "collector-30", "pc-collector-00", "pc-collector-30", "phone-collector-00"}

def fallback(at, reason):
    return {"at": at, "offers": [], "metadata": {"status": "research_failed", "eligibleCount": 0, "target": 20, "minimum": 10, "storesSearched": [], "blockers": [reason]}}

def append(doc, run):
    if not isinstance(doc.get("runs"), list):
        raise ValueError("existing history invalid")
    if not any(r["at"] == run["at"] for r in doc["runs"]):
        doc["runs"].append(run)
    return doc

def request(path, method="GET", body=None):
    url = "https://api.github.com/repos/" + os.environ["GITHUB_REPOSITORY"] + "/" + path
    headers = {"Authorization": "Bearer " + os.environ["GH_TOKEN"], "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "BlackFridayManager"}
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=25) as response:
        return json.load(response)

def read(path):
    blob = request(path + "?ref=main")
    return blob["sha"], json.loads(base64.b64decode(blob["content"]))

def publish(feed, run):
    path = "contents/data/" + feed + ".json"
    for attempt in range(5):
        try:
            sha, doc = read(path)
            existing = next((r for r in doc["runs"] if r["at"] == run["at"]), None)
            if existing is not None:
                if existing != run:
                    raise ValueError("timestamp collision with different snapshot")
                # Verify actual commit for idempotent retry.
                commits = request("commits?sha=main&path=data%2F" + feed + ".json&per_page=1")
                return commits[0]["sha"], sha
            append(doc, run)
            content = base64.b64encode((json.dumps(doc, ensure_ascii=False, indent=2) + "\n").encode()).decode()
            result = request(path, "PUT", {"message": "data: refresh " + feed + " " + run["at"] + " (Manaus)", "content": content, "sha": sha, "branch": "main"})
            reread_sha, reread = read(path)
            if not any(r == run for r in reread["runs"]):
                raise RuntimeError("snapshot missing after commit")
            return result["commit"]["sha"], reread_sha
        except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            print("Publish attempt", attempt + 1, type(exc).__name__, getattr(exc, "code", ""), flush=True)
            if attempt == 4:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError("publication failed")

def report(feed, run, commit, blob):
    m = run["metadata"]
    lines = [f"### {feed}", f"- Verified: {m['eligibleCount']}/20 ({m['eligibleCount']*5}%)", f"- Status: {m['status']}", f"- Commit: {commit}", f"- Blob: {blob}", f"- Stores: {', '.join(m['storesSearched']) or 'none confirmed'}", f"- New/changed/unchanged: {m.get('newLinks', 0)}/{m.get('changedPrices', 0)}/{m.get('unchangedPrices', 0)}"]
    available = [o for o in run["offers"] if o["inStock"] and o.get("eligible", True)]
    if feed.startswith("collector-"):
        base = min((o for o in available if not o.get("games")), key=lambda o:o["price"], default=None)
        bundle = min((o for o in available if o.get("games")), key=lambda o:o["price"], default=None)
        best = bundle if bundle and (not base or bundle["price"] <= base["price"]*1.10) else base
        for label, o in (("Standalone", base), ("Bundle", bundle), ("Recommended", best)):
            lines.append(f"- {label}: R$ {o['price']:.2f} — {o['store']} — {o['url']}" if o else f"- {label}: not verified")
    else:
        best = min(available, key=lambda o:o["price"], default=None)
        if best:
            lines.append(f"- Best: R$ {best['price']:.2f} — {best['url']}")
    lines.extend(["- Coupons: no independently verified coupon applied", "- Blockers: " + "; ".join(m["blockers"]), "- Dashboard: https://black-friday-manager-kindermanbarros-projects.vercel.app"])
    report_text = "\n".join(lines) + "\n"
    print(report_text)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as out:
            out.write(report_text)

if __name__ == "__main__":
    feed, at, filename = sys.argv[1:]
    if feed not in FEEDS:
        raise SystemExit("invalid feed")
    try:
        run = json.loads(Path(filename).read_text(encoding="utf-8"))
        if run["at"] != at or not isinstance(run["offers"], list) or not isinstance(run["metadata"], dict):
            raise ValueError("invalid snapshot")
    except (OSError, ValueError, KeyError, TypeError):
        run = fallback(at, "research step failed or timed out before writing a valid snapshot")
    commit, blob = publish(feed, run)
    report(feed, run, commit, blob)
