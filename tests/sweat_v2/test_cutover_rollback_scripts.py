import json
import os
import subprocess


def test_cutover_dry_run_reports_not_ready_by_default() -> None:
    env = os.environ.copy()
    env.pop("SWEAT_V2_ENABLED", None)
    env.pop("SWEAT_V2_SHADOW_MODE", None)
    proc = subprocess.run(
        ["python3", "scripts/sweat_v2_cutover_dry_run.py"],
        cwd="/home/claw-admin/.openclaw/workspace/projects/SWEAT",
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode in {0, 2}
    path = proc.stdout.strip().splitlines()[0]
    data = json.loads(open(path).read())
    assert data["mode"] == "cutover_dry_run"


def test_rollback_dry_run_writes_report() -> None:
    proc = subprocess.run(
        ["python3", "scripts/sweat_v2_rollback_dry_run.py"],
        cwd="/home/claw-admin/.openclaw/workspace/projects/SWEAT",
        capture_output=True,
        text=True,
        check=True,
    )
    path = proc.stdout.strip().splitlines()[0]
    data = json.loads(open(path).read())
    assert data["mode"] == "rollback_dry_run"
