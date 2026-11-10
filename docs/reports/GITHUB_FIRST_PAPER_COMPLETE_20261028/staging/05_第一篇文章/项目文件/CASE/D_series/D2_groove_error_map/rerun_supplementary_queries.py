#!/usr/bin/env python3
"""Re-run of the supplementary literature queries (TS1' / TS2' / TS3 / TS4).

Why this exists
---------------
The original 18-query batch (task B) had three limitations that were measured,
not guessed:
  1. a `from_publication_date=2005-01-01` floor, which excludes Patir & Cheng
     (1978) - the origin of the closure being compared;
  2. a title screen that required a geometry word, which drops papers whose
     titles only say "hydrodynamic lubrication" / "flow factors" /
     "transmissivity averaging";
  3. no query containing the equivalent names of the closure.

This script re-runs four queries that fix all three.  Time is unrestricted.

Query translation
-----------------
OpenAlex `title_and_abstract.search` treats space-separated words as AND and
supports quoted phrases and `|` for OR.  Repeating the filter key gives AND
between groups.  So the WoS-style queries map directly:

    filter=title_and_abstract.search:"flow factor"|"average flow model"
          ,title_and_abstract.search:groove|ridge|rectangular

is  ("flow factor" OR "average flow model") AND (groove OR ridge OR rectangular).

Outputs (in ./rerun2/):
  TS1p.json TS2p.json TS3.json TS4.json   raw hits per query
  rerun2_summary.md                        human-readable screen result
"""

import json
import os
import re
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "rerun2")
os.makedirs(OUT, exist_ok=True)

SELECT = ("id,doi,title,publication_year,primary_location,"
          "abstract_inverted_index,cited_by_count,type,authorships")

# ---------------------------------------------------------------------------
# the four queries.  Each entry: (tag, label, [group1, group2, ...])
# a group is an OR-list; groups are ANDed.
# ---------------------------------------------------------------------------
QUERIES = [
    ("TS1p", "permeability + groove + tensor/anisotropic + method", [
        'permeability|"hydraulic conductance"',
        'groove|corrugat|trench|"line and space"|ridge',
        '"permeability tensor"|anisotropic|"principal direction"|"two principal"',
        'numerical|simulation|"finite element"|stokes|"lattice boltzmann"',
    ]),
    ("TS2p", "nanoimprint filling / effective transport", [
        'nanoimprint|"UV-NIL"|"imprint lithography"',
        '"filling time"|"feature filling"|"residual layer"|"flow model"|"effective transport"',
    ]),
    ("TS3", "flow factor / average flow model (no time floor, no method word)", [
        '"flow factor"|"average flow model"|"averaged Reynolds"',
        'groove|ridge|rectangular|"transverse roughness"',
    ]),
    ("TS4", "transmissivity averaging / homogenization", [
        '"transmissivity averaging"|"arithmetic harmonic"|homogenization',
        'groove|channel|aperture',
        'numerical|comparison|error',
    ]),
]

NOISE = re.compile(
    r"aquifer|levee|landfill|slurry|cutoff wall|seepage|subduction|groundwater|"
    r"pavement|tailings|coning|hydraulic fractur|shale|reservoir|coal seam|"
    r"cancer|peptide|protein|drug|virus|anticancer|"
    r"gas.?permeable|transistor|waveguide|ferrite|metamaterial|plasmon|polarizer",
    re.I)

RELEVANT = re.compile(
    r"groove|corrugat|trench|ridge|rectangular|transverse roughness|"
    r"flow factor|average flow model|transmissivity|homogeniz|"
    r"permeabilit|lubricat|clutch|bearing|seal|stokes|reynolds", re.I)


def fetch_all(filters, page_size=200, max_pages=15):
    """Fetch every record matching the AND of the given groups."""
    filt = ",".join("title_and_abstract.search:" + g for g in filters)
    url_base = ("https://api.openalex.org/works?filter="
                + urllib.parse.quote(filt, safe=":,|")
                + f"&per-page={page_size}&select={SELECT}")
    out, page, total, err = [], 1, None, None
    while page <= max_pages:
        url = url_base + f"&page={page}"
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "sim240-lit/1.0 (mailto:research@example.org)"})
            with urllib.request.urlopen(req, timeout=90) as r:
                d = json.load(r)
        except Exception as e:
            err = f"page {page}: {e}"
            break
        if total is None:
            total = d["meta"]["count"]
        res = d["results"]
        out += res
        if not res or len(out) >= total:
            break
        page += 1
        time.sleep(0.35)
    return out, total, err, url_base


def abstract(w):
    inv = w.get("abstract_inverted_index") or {}
    pos = [(i, wd) for wd, idxs in inv.items() for i in idxs]
    return " ".join(wd for _, wd in sorted(pos))


def blob(w):
    return ((w.get("title") or "") + " " + abstract(w))


def main():
    results = {}
    for tag, label, groups in QUERIES:
        hits, total, err, url = fetch_all(groups)
        results[tag] = {"label": label, "groups": groups, "total": total,
                        "fetched": len(hits), "error": err, "url": url,
                        "hits": hits}
        print(f"{tag:6s} total={total:5} fetched={len(hits):5} "
              f"{'ERR ' + err if err else ''}  {label}")
        time.sleep(0.5)

    for tag, v in results.items():
        with open(os.path.join(OUT, f"{tag}.json"), "w", encoding="utf-8") as f:
            json.dump(v, f, ensure_ascii=False)

    # ---------------- screen ----------------
    lines = []
    def say(s=""):
        print(s)
        lines.append(s)

    say("# Supplementary query re-run (TS1' / TS2' / TS3 / TS4)")
    say()
    say("Generated by `rerun_supplementary.py`. Time unrestricted (no 2005 floor).")
    say()
    say("| query | meaning | total | fetched |")
    say("|---|---|---|---|")
    for tag, v in results.items():
        say(f"| {tag} | {v['label']} | {v['total']} | {v['fetched']} |")
    say()

    all_seen = {}
    for tag, v in results.items():
        kept, noise = [], []
        for w in v["hits"]:
            b = blob(w)
            (noise if NOISE.search(b) else kept).append(w)
        say(f"## {tag} - {v['label']}")
        say()
        say(f"raw {len(v['hits'])}  ->  after noise removal {len(kept)}  "
            f"(noise {len(noise)})")
        say()
        for w in sorted(kept, key=lambda x: (x.get("publication_year") or 0)):
            au = [a["author"]["display_name"] for a in w.get("authorships", [])][:3]
            ven = ((w.get("primary_location") or {}).get("source") or {}).get("display_name") or "?"
            say(f"- **{w.get('publication_year')}** | {w.get('title')}")
            say(f"  - {', '.join(au)} | {ven} | {w.get('doi')} | cited {w.get('cited_by_count')}")
            all_seen[w["id"]] = w
        say()

    say(f"## Union\n\n{len(all_seen)} unique records across the four queries.")
    with open(os.path.join(OUT, "rerun2_summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\nwritten:", os.path.join(OUT, "rerun2_summary.md"))


if __name__ == "__main__":
    main()
