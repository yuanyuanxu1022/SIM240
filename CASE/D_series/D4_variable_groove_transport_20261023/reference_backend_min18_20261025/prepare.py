#!/usr/bin/env python3
"""Preparation only. No argument, option or input can launch a solver."""
import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from contract import Rejected, select
from records import stage


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--mode", choices=("check", "describe", "stage"), default="check")
    parser.add_argument("--planned-id")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--prep-id")
    parser.add_argument("--output-parent", type=Path)
    args = parser.parse_args(argv)
    try:
        def unique_object(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise Rejected("DUPLICATE_JSON_KEY")
                result[key] = value
            return result
        supplied = json.loads(args.config.read_text(), object_pairs_hook=unique_object) if args.config else None
        if args.config and not isinstance(supplied, dict):
            raise Rejected("CONFIG_MUST_BE_AN_OBJECT")
        plans = select(args.planned_id, supplied)
        if args.mode != "stage" and (args.prep_id or args.output_parent):
            raise Rejected("OUTPUT_ARGUMENTS_REQUIRE_STAGE_MODE")
        if args.mode == "stage":
            destination, status = stage(plans, args.prep_id, args.output_parent)
            payload = {"kind": "PREPARATION_ONLY", "directory": str(destination),
                       "problem_count": len(plans), "preparation_complete": status["preparation_complete"]}
        elif args.mode == "describe":
            payload = {"kind": "STATIC_DESCRIPTION", "plans": plans}
        else:
            payload = {"kind": "STATIC_INPUT_CHECK", "input_check_ok": True,
                       "problem_count": len(plans), "planned_ids": [p["planned_id"] for p in plans]}
        payload.update(solver_called=False, actual_run_id=None,
                       execution_authorized=False, numerical_acceptance="NOT_EVALUATED")
        print(json.dumps(payload, indent=2, allow_nan=False))
        return 0
    except (Rejected, OSError, ValueError, TypeError) as exc:
        print(json.dumps({"kind": "PREPARATION_REJECTED", "reason": str(exc),
                          "solver_called": False, "execution_authorized": False}), file=sys.stderr)
        return 64


if __name__ == "__main__":
    sys.exit(main())
