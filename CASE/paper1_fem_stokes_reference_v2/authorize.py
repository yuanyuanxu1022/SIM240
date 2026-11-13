#!/usr/bin/env python3
"""Record an explicit authorization for a subset of the frozen point set.

Running is refused unless an authorization exists and matches the current
release digest. This keeps "the point set is frozen" and "the author said go"
as two separate, auditable facts.

Usage
    python3 authorize.py --list
    python3 authorize.py --grant h50_d25_T h50_d50_T --note "last limited round"
    python3 authorize.py --grant all --hold h25_d25_T h25_d50_T --note "..."
"""
from __future__ import annotations

import argparse
import json
import sys

import receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--grant", nargs="*", default=None)
    parser.add_argument("--hold", nargs="*", default=None)
    parser.add_argument("--note", default="")
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    points = receipt.load_points()["points"]
    eligible = [p["case"] for p in points if p.get("status") == "ELIGIBLE"]
    blocked = [p["case"] for p in points if p.get("status") != "ELIGIBLE"]

    if args.list:
        current = receipt.load_authorization()
        print(json.dumps({
            "eligible": eligible,
            "blocked": blocked,
            "authorization": current,
            "release_sha256": (receipt.release_digest()
                               if receipt.MANIFEST_PATH.exists() else None),
        }, indent=2, ensure_ascii=False))
        return 0

    if args.grant is None:
        parser.error("choose --list or --grant")

    granted = eligible if args.grant == ["all"] else list(args.grant)
    held = list(args.hold or [])
    unknown = [c for c in granted + held if c not in eligible + blocked]
    if unknown:
        print(f"unknown cases: {unknown}")
        return receipt.EXIT_BAD_INPUT
    not_eligible = [c for c in granted if c in blocked]
    if not_eligible:
        print(f"refusing to authorize points whose status is not ELIGIBLE: {not_eligible}")
        return receipt.EXIT_BAD_INPUT
    if not args.note.strip():
        print("a written note is required so the authorization is self-explanatory")
        return receipt.EXIT_BAD_INPUT
    if receipt.AUTHORIZATION_PATH.exists() and not args.replace:
        print("authorization.json exists; use --replace to supersede it")
        return receipt.EXIT_BAD_INPUT

    try:
        digest = receipt.release_digest()
    except receipt.ReleaseDrift as error:
        print(f"cannot authorize against an unverifiable release: {error}")
        return receipt.EXIT_RELEASE_DRIFT

    payload = {
        "schema": "sim240_fem_authorization/1",
        "recorded_at": receipt.utcnow(),
        "release_sha256": digest,
        "granted_cases": sorted(granted),
        "held_cases": sorted(held),
        "note": args.note.strip(),
        "scope": ("this authorization covers one solve plus one independent "
                  "verification per granted case, three mesh levels each; it does "
                  "not authorize mesh refinement, new geometries or a second run"),
    }
    path = receipt.AUTHORIZATION_PATH
    digest_of_file = receipt.atomic_write_json(path, payload)
    print(json.dumps({"written": str(path), "file_sha256": digest_of_file,
                      "granted": payload["granted_cases"],
                      "held": payload["held_cases"],
                      "release_sha256": digest}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
