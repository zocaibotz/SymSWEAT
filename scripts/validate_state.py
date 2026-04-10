import argparse
import json
import os
import sys
from pathlib import Path

from jsonschema import validate, ValidationError


def _load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    ap = argparse.ArgumentParser(description="Validate SWEAT state artifacts against JSON schemas")
    ap.add_argument("--project-dir", required=True)
    args = ap.parse_args()

    pdir = Path(args.project_dir)
    state_dir = pdir / "state"
    ps_path = state_dir / "project_state.json"
    re_path = state_dir / "run_events.jsonl"

    ps_schema = _load("schemas/project_state.schema.json")
    re_schema = _load("schemas/run_event.schema.json")

    errors = []

    if not ps_path.exists():
        errors.append(f"missing: {ps_path}")
    else:
        try:
            validate(instance=_load(ps_path), schema=ps_schema)
        except ValidationError as e:
            errors.append(f"project_state invalid: {e.message}")

    if not re_path.exists():
        errors.append(f"missing: {re_path}")
    else:
        with open(re_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    evt = json.loads(line)
                    validate(instance=evt, schema=re_schema)
                except Exception as e:
                    errors.append(f"run_events line {i} invalid: {e}")
                    break

    if errors:
        for e in errors:
            print("FAIL", e)
        return 1

    print("PASS state schema validation")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
