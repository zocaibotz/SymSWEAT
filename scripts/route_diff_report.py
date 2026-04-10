import argparse
import json
from pathlib import Path


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def nodes(seq):
    return [x.get("node") for x in seq if x.get("node")]


def main():
    ap = argparse.ArgumentParser(description="Compare two strict E2E route traces")
    ap.add_argument("--base", required=True)
    ap.add_argument("--head", required=True)
    ap.add_argument("--out", default="reports/runs/route_diff_report.md")
    args = ap.parse_args()

    b = load(args.base)
    h = load(args.head)
    bn = nodes(b.get("route", []))
    hn = nodes(h.get("route", []))

    bset, hset = set(bn), set(hn)
    added = sorted(hset - bset)
    removed = sorted(bset - hset)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "# Route Diff Report\n\n"
        f"- base: `{args.base}`\n"
        f"- head: `{args.head}`\n"
        f"- base_steps: {len(bn)}\n"
        f"- head_steps: {len(hn)}\n\n"
        f"## Added nodes\n{added}\n\n"
        f"## Removed nodes\n{removed}\n\n"
        f"## Base final_next_agent\n`{b.get('final_next_agent')}`\n\n"
        f"## Head final_next_agent\n`{h.get('final_next_agent')}`\n",
        encoding="utf-8",
    )

    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
