import json
import os
import sys


def main():
    if len(sys.argv) < 3:
        print("usage: validate_strict_e2e.py <run_events.jsonl> <run_id>")
        return 2

    path, run_id = sys.argv[1], sys.argv[2]
    if not os.path.exists(path):
        print(f"FAIL missing events: {path}")
        return 1

    seq = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                evt = json.loads(line)
            except Exception:
                continue
            if evt.get("run_id") == run_id and evt.get("event_type") == "route_decision":
                nxt = ((evt.get("payload") or {}).get("next_node"))
                if nxt:
                    seq.append(nxt)

    if not seq:
        print("FAIL no route_decision events for run")
        return 1

    required = ["sdd_specify", "sdd_plan", "sdd_tasks", "architect", "tdd_orchestrator", "pipeline"]
    missing = [x for x in required if x not in seq]
    if missing:
        print(f"FAIL missing required path nodes: {missing}")
        return 1

    # detect pathological req/spec loops
    loop_count = 0
    for i in range(1, len(seq)):
        if (seq[i-1], seq[i]) in {("req_master_interview", "sdd_specify"), ("sdd_specify", "req_master_interview")}:
            loop_count += 1
    if loop_count > 6:
        print(f"FAIL excessive req/spec loop transitions: {loop_count}")
        return 1

    print("PASS strict e2e route checklist")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
