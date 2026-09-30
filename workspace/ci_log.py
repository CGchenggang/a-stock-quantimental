"""Download the failing CI job log for a commit and show failure lines."""
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request

token = sys.argv[1]
sha = sys.argv[2]
headers = {"User-Agent": "ci-debug", "Authorization": f"Bearer {token}"}


def api(url):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def get_log(url):
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None
    opener = urllib.request.build_opener(NoRedirect)
    try:
        opener.open(urllib.request.Request(url, headers=headers), timeout=60)
        raise RuntimeError("expected 302")
    except urllib.error.HTTPError as e:
        location = e.headers["Location"]
    req = urllib.request.Request(location)  # signed URL: no auth header
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read().decode("utf-8", errors="replace")


runs = api(f"https://api.github.com/repos/CGchenggang/a-stock-quantimental/actions/runs?head_sha={sha}")
run = runs["workflow_runs"][0]
print("RUN", run["id"], run["conclusion"])
jobs = api(f"https://api.github.com/repos/CGchenggang/a-stock-quantimental/actions/runs/{run['id']}/jobs")
fail = [j for j in jobs["jobs"] if j["conclusion"] == "failure"][0]
print("FAIL JOB:", fail["name"], fail["id"])
log = get_log(f"https://api.github.com/repos/CGchenggang/a-stock-quantimental/actions/jobs/{fail['id']}/logs")
lines = log.splitlines()
idxs = [i for i, l in enumerate(lines) if "FAILED" in l or re.search(r"\d+ failed", l)]
start = max(0, (idxs[0] - 5)) if idxs else len(lines) - 50
shown = 0
for line in lines[start:]:
    print(line[:250])
    shown += 1
    if shown > 60:
        break
