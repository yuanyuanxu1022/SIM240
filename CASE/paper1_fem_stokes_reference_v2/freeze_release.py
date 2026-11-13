#!/usr/bin/env python3
"""Bind the package into an immutable release manifest before any run.

The manifest records, for every packaged file, its size and sha256, plus the
gated dependency versions and the digests of the point set and acceptance rule.
``receipt.verify_release()`` recomputes all of it at run time and refuses to
start on any drift.

Usage
    python3 freeze_release.py --write --reason "initial freeze"
    python3 freeze_release.py --check
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import receipt

def build_manifest(reason: str) -> dict:
    missing = [name for name in ("PROTOCOL.md", "points.json", "acceptance_rule.json",
                                 "fem_pilot.py", "verify_results.py", "receipt.py")
               if not (receipt.PACKAGE / name).exists()]
    if missing:
        raise SystemExit(f"cannot freeze, missing packaged files: {missing}")

    entries = [{"path": str(path.relative_to(receipt.PACKAGE)),
                "bytes": path.stat().st_size,
                "sha256": receipt.sha256_file(path)} for path in receipt.collect_files()]
    body = {
        "schema": receipt.SCHEMA_RELEASE,
        "package": receipt.PACKAGE.name,
        "frozen_at": receipt.utcnow(),
        "reason": reason,
        "files": entries,
        "environment": receipt.environment_snapshot(),
        "point_set_sha256": receipt.sha256_file(receipt.POINTS_PATH),
        "acceptance_rule_sha256": receipt.sha256_file(receipt.RULE_PATH),
        "solver_is_byte_identical_to": None,
        "note": "Checking this manifest does not grant any numerical or reference "
                "status. It only proves the package did not change between freeze "
                "and run.",
    }
    v1 = receipt.PACKAGE.parent / "paper1_fem_stokes_pilot_v1"
    if (v1 / "fem_pilot.py").exists():
        same_solver = receipt.sha256_file(v1 / "fem_pilot.py") == receipt.sha256_file(
            receipt.PACKAGE / "fem_pilot.py")
        same_verifier = receipt.sha256_file(v1 / "verify_results.py") == receipt.sha256_file(
            receipt.PACKAGE / "verify_results.py")
        body["solver_is_byte_identical_to"] = {
            "package": "paper1_fem_stokes_pilot_v1",
            "fem_pilot.py": same_solver,
            "verify_results.py": same_verifier,
        }
    body["release_sha256"] = receipt.digest_of(body)
    return body


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--rewrite", action="store_true",
                        help="replace an existing manifest (invalidates every authorization)")
    parser.add_argument("--reason", default="")
    args = parser.parse_args()

    if args.check:
        try:
            manifest = receipt.verify_release()
        except receipt.ReleaseDrift as error:
            print(f"RELEASE_DRIFT: {error}")
            return receipt.EXIT_RELEASE_DRIFT
        print(f"RELEASE_OK {manifest['release_sha256']} files={len(manifest['files'])}")
        return 0

    if not args.write:
        parser.error("choose --write or --check")

    existing = receipt.MANIFEST_PATH
    if existing.exists() and not args.rewrite:
        print(f"refusing to overwrite {existing}; use --rewrite with a written reason")
        return receipt.EXIT_BAD_INPUT
    if not args.reason.strip():
        print("a freeze reason is required")
        return receipt.EXIT_BAD_INPUT

    manifest = build_manifest(args.reason.strip())
    receipt.atomic_write_json(existing, manifest)
    log = receipt.PACKAGE / "FREEZE_LOG.md"
    line = (f"- {manifest['frozen_at']} release `{manifest['release_sha256']}` "
            f"files={len(manifest['files'])} reason: {manifest['reason']}\n")
    if log.exists():
        log.write_text(log.read_text() + line)
    else:
        log.write_text("# Freeze log\n\n" + line)
    print(json.dumps({"release_sha256": manifest["release_sha256"],
                      "files": len(manifest["files"]),
                      "solver_byte_identical": manifest["solver_is_byte_identical_to"]},
                     indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
