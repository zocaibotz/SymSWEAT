import sys
import os
import json
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.tools.security_remediation import SecurityRemediationEngine


def test_security_remediation_plan_generation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    d = tmp_path / "reports" / "security"
    d.mkdir(parents=True, exist_ok=True)

    (d / "pip_audit_before.json").write_text(json.dumps({
        "dependencies": [
            {"name": "foo", "vulns": [{"id": "CVE-1"}]},
            {"name": "bar", "vulns": []},
        ]
    }))
    (d / "bandit_before.json").write_text(json.dumps({
        "results": [
            {"issue_severity": "MEDIUM", "test_id": "B603", "filename": "x.py", "line_number": 10}
        ]
    }))
    (d / "detect_secrets_before.baseline").write_text(json.dumps({
        "results": {".env": [{"type": "Secret Keyword"}]}
    }))

    engine = SecurityRemediationEngine()
    plan = engine.build_plan()

    assert plan["dependency_remediation"]["count"] == 1
    assert plan["bandit_remediation"]["manual_review_required"] is True
    assert plan["secret_remediation"]["hard_fail"] is True
    assert (d / "remediation_plan.json").exists()
