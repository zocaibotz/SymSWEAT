import os
import sys
import json
from datetime import datetime, timezone

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.tools.linear import LinearClient


def row(name, ok, detail=None):
    return {"check": name, "pass": bool(ok), "detail": detail}


def main():
    c = LinearClient()
    out = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "env": {
            "has_LINEAR_API_KEY": bool(os.getenv("LINEAR_API_KEY")),
            "has_LINEAR_TEAM_ID": bool(os.getenv("LINEAR_TEAM_ID")),
        },
        "checks": [],
    }

    # 1) Diagnostics
    d = c._diagnostics(require_team=True)
    out["checks"].append(row("diagnostics.api_key_present", d.get("has_api_key"), d))
    out["checks"].append(row("diagnostics.team_id_present", d.get("has_team_id"), d))

    # 2) Viewer auth sanity (raw GraphQL)
    raw = c._query("query { viewer { id name email } }")
    viewer = (((raw or {}).get("data") or {}).get("viewer") or {})
    out["checks"].append(row("viewer_query", bool(viewer.get("id")), viewer or raw.get("errors")))

    # 3) Team states
    st = c.list_workflow_states()
    out["checks"].append(row("list_workflow_states", st.get("success"), st.get("error") or {"count": len(st.get("states") or [])}))

    # 4) Project lookup
    p = c.find_project_by_name("SWEAT")
    out["checks"].append(row("find_project_by_name:SWEAT", p.get("success"), (p.get("project") or {}).get("id") or p.get("error")))

    # 5) Project issues list (if project found)
    if p.get("success") and p.get("project"):
        pid = p["project"]["id"]
        li = c.list_project_issues(project_id=pid, first=10)
        out["checks"].append(row("list_project_issues:SWEAT", li.get("success"), li.get("error") or {"count": len(li.get("issues") or [])}))

    # 6) Issue lookup by TEAM-NUM
    for ident in ["ZOC-29", "ZOC-30", "ZOC-31", "ZOC-32"]:
        gi = c.get_issue(ident)
        out["checks"].append(row(f"get_issue:{ident}", gi.get("success"), gi.get("error") or ((gi.get("issue") or {}).get("id"))))

    # 7) Transition smoke test (idempotent-ish: set started)
    t = c.transition_issue("ZOC-29", "started")
    out["checks"].append(row("transition_issue:ZOC-29->started", t.get("success"), t.get("error") or ((t.get("issue") or {}).get("state") or {}).get("type")))

    out["summary"] = {
        "total": len(out["checks"]),
        "passed": sum(1 for x in out["checks"] if x["pass"]),
        "failed": sum(1 for x in out["checks"] if not x["pass"]),
    }

    os.makedirs("reports", exist_ok=True)
    path = "reports/linear_permission_check.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(path)
    print(json.dumps(out["summary"]))


if __name__ == "__main__":
    main()
