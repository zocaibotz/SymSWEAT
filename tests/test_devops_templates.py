import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.tools.devops import ci_template


def test_strict_ci_template_contains_required_jobs():
    t = ci_template("python", strict=True)
    assert "jobs:" in t
    assert "unit:" in t
    assert "integration:" in t
    assert "e2e_playwright:" in t
    assert "security:" in t
    assert "Initial security scan (before remediation)" in t
    assert "Build remediation policy plan" in t
    assert "scripts/security_remediation_plan.py" in t
    assert "Auto-remediation attempt (safe)" in t
    assert "Rescan after remediation" in t
    assert "security_remediation_report.md" in t
    assert "Publish PR security summary" in t
    assert "$GITHUB_STEP_SUMMARY" in t
    assert "deploy_staging:" in t
    assert "deploy_prod:" in t
    assert "matrix:" in t
    assert "cache: 'pip'" in t
    assert "cache: 'npm'" in t
    assert "|| true" not in t
