import json
import subprocess
from pathlib import Path


def test_promotion_evidence_gate_outputs_report() -> None:
    proc = subprocess.run(
        ["python3", "scripts/sweat_v2_promotion_evidence_gate.py"],
        cwd="/home/claw-admin/.openclaw/workspace/projects/SWEAT",
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode in {0, 2}
    path = proc.stdout.strip().splitlines()[0]
    data = json.loads(Path(path).read_text())
    assert "shadow_rows" in data
    assert "ready" in data
