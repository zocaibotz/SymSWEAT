import json
from pathlib import Path
from typing import Dict, Any


class SecurityRemediationEngine:
    """
    Policy-driven safe remediation planner/executor.

    v1 policy:
    - pip-audit vulnerabilities: recommend/attempt dependency upgrade path
    - bandit findings: classify actionable vs manual-review
    - detect-secrets findings: classify as hard-fail/manual-review
    """

    def __init__(self):
        self.report_dir = Path("reports/security")

    def _load_json(self, p: Path, default):
        if not p.exists():
            return default
        try:
            return json.loads(p.read_text())
        except Exception:
            return default

    def build_plan(self) -> Dict[str, Any]:
        pip_before = self._load_json(self.report_dir / "pip_audit_before.json", {"dependencies": []})
        bandit_before = self._load_json(self.report_dir / "bandit_before.json", {"results": []})
        secret_before = self._load_json(self.report_dir / "detect_secrets_before.baseline", {"results": {}})

        deps = pip_before.get("dependencies", []) if isinstance(pip_before, dict) else pip_before
        vuln_deps = [d for d in deps if d.get("vulns")]

        bandit_results = bandit_before.get("results", [])
        bandit_actionable = [
            r for r in bandit_results
            if r.get("issue_severity") in {"HIGH", "MEDIUM"}
        ]

        secret_hits = sum(len(v) for v in (secret_before.get("results") or {}).values())

        plan = {
            "dependency_remediation": {
                "count": len(vuln_deps),
                "targets": [d.get("name") for d in vuln_deps],
                "strategy": "pip install --upgrade -r requirements.txt",
            },
            "bandit_remediation": {
                "manual_review_required": len(bandit_actionable) > 0,
                "findings": [
                    {
                        "test_id": r.get("test_id"),
                        "file": r.get("filename"),
                        "line": r.get("line_number"),
                        "severity": r.get("issue_severity"),
                    }
                    for r in bandit_actionable
                ],
            },
            "secret_remediation": {
                "hard_fail": secret_hits > 0,
                "hits": secret_hits,
                "strategy": "manual secret cleanup + key rotation required",
            },
        }

        self.report_dir.mkdir(parents=True, exist_ok=True)
        (self.report_dir / "remediation_plan.json").write_text(json.dumps(plan, indent=2))
        return plan


_engine = SecurityRemediationEngine()


def get_security_remediation_engine() -> SecurityRemediationEngine:
    return _engine
