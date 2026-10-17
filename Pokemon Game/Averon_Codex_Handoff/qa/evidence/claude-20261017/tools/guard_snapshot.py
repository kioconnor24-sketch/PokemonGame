"""Rebuild the exclusive-files guard input for one PR from live REST data (manual paging)."""
import json, re, subprocess, sys
R = "repos/kioconnor24-sketch/PokemonGame"
def api_all(path):
    items, page = [], 1
    sep = "&" if "?" in path else "?"
    while True:
        out = json.loads(subprocess.check_output(["gh", "api", f"{path}{sep}per_page=100&page={page}"]))
        items += out
        if len(out) < 100:
            return items
        page += 1
number = int(sys.argv[1])
own = api_all(f"{R}/pulls/{number}/files")
others = []
for p in api_all(f"{R}/pulls?state=open"):
    if p["number"] != number:
        files = api_all(f"{R}/pulls/{p['number']}/files")
        others.append({"number": p["number"], "files": [f["filename"] for f in files if f["status"] != "removed"]})
handoffs = []
rx = re.compile(r"^HANDOFF_APPROVED PR=#(\d+) PATHS=([^\r\n]+)$", re.M)
for c in api_all(f"{R}/issues/15/comments"):
    if c["author_association"] in ("OWNER", "MEMBER", "COLLABORATOR"):
        for m in rx.finditer(c.get("body") or ""):
            handoffs.append({"pr": int(m.group(1)), "paths": [x.strip() for x in m.group(2).split(",")],
                             "association": c["author_association"]})
json.dump({"pull_request": {"number": number, "files": [{"filename": f["filename"], "status": f["status"]} for f in own]},
           "other_open_prs": others, "handoffs": handoffs}, sys.stdout, indent=1)
