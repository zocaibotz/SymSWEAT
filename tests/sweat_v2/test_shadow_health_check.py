import json
import os
import subprocess
from pathlib import Path


def test_shadow_health_check_fails_when_enabled_and_empty(tmp_path: Path) -> None:
    env = os.environ.copy()
    env["SWEAT_V2_ENABLED"] = "true"
    env["SWEAT_V2_SHADOW_MODE"] = "true"
    proc = subprocess.run(
        ["python3", "scripts/sweat_v2_shadow_health_check.py"],
        cwd="/home/claw-admin/.openclaw/workspace/projects/SWEAT",
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode in {0, 2}
    path = proc.stdout.strip().splitlines()[0]
    data = json.loads(open(path).read())
    if data["rows"] == 0:
        assert proc.returncode == 2


def test_shadow_health_check_passes_when_disabled() -> None:
    env = os.environ.copy()
    env["SWEAT_V2_ENABLED"] = "false"
    env["SWEAT_V2_SHADOW_MODE"] = "true"
    proc = subprocess.run(
        ["python3", "scripts/sweat_v2_shadow_health_check.py"],
        cwd="/home/claw-admin/.openclaw/workspace/projects/SWEAT",
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
