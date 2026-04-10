import os
import subprocess
from typing import Dict, Any


class SpecifyRunner:
    def __init__(self):
        self.cmd = os.getenv("SWEAT_SPECIFY_CMD", "specify")

    def _run(self, args: list[str], cwd: str = ".") -> subprocess.CompletedProcess:
        return subprocess.run([self.cmd, *args], cwd=cwd, capture_output=True, text=True)

    def run_specify_flow(self, cwd: str = ".") -> Dict[str, Any]:
        """
        Try real specify CLI flow; fallback gracefully if command unavailable.
        """
        check = subprocess.run(["bash", "-lc", f"command -v {self.cmd}"], cwd=cwd, capture_output=True, text=True)
        if check.returncode != 0:
            return {"success": False, "error": f"{self.cmd} not found"}

        out = {}
        for step in ["specify", "plan", "tasks"]:
            r = self._run([step], cwd=cwd)
            out[step] = {"code": r.returncode, "stdout": r.stdout[-800:], "stderr": r.stderr[-800:]}
            if r.returncode != 0:
                return {"success": False, "step": step, "details": out}

        return {"success": True, "details": out}


_specify_runner = SpecifyRunner()


def get_specify_runner() -> SpecifyRunner:
    return _specify_runner
