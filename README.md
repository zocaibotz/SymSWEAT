# SWEAT (SoftWare Engineering Agentic Titan) 🗿

**Version 1.0.0**

A multi-agent autonomous software engineering firm orchestrated by **Zocai**.

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Git
- API Keys (Gemini, OpenAI, or Anthropic)

### Installation
1. Clone the repo.
2. Run setup:
   ```bash
   ./setup.sh
   ```
3. Configure `.env`:
   ```bash
   cp .env.example .env
   # Edit .env with your keys
   ```
   Reference: `docs/ENVIRONMENT_VARIABLES.md`

### Running
```bash
./run.sh
```

### Monitoring command center API (Project 1)
```bash
source .venv/bin/activate
uvicorn src.app:app --host 0.0.0.0 --port 8000
```

Then use:
- `GET /api/monitoring/projects`
- `GET /api/monitoring/projects/{project_id}`
- `GET /api/monitoring/stream?project_id=...` (SSE live events)

## 🏗️ Architecture

### Agents
| Agent | Role | Tools |
| :--- | :--- | :--- |
| **Zocai** | Orchestrator | Context Pruning, Routing |
| **ReqMaster** | Product Manager | Requirements Analysis |
| **Architech** | Architect | System Design |
| **CodeSmith** | Developer | FileSystem, Git, Codex/Gemini |
| **Gatekeeper** | Reviewer | Git Diff Analysis |
| **PipeLine** | DevOps | Pytest, CI Checks |
| **Deployer** | Ops | K8s/Docker Manifests |

### Tooling
- **LLM Routing**: 
  - Main: Gemini API (Default) -> CLI -> Mock
  - Coder: Codex CLI (Optional) -> Gemini API -> Mock
- **FileSystem**: Sandboxed local read/write.
- **Git**: Automated commit/diff with agent personas.

## 🧪 Testing
Run the integration suite:
```bash
pytest tests/test_integration.py
```

### Strict E2E acceptance check
Generate a machine-readable strict E2E validation artifact for the latest run:
```bash
python scripts/run_strict_e2e_check.py --project-dir projects/overnight-e2e-01
```

Output artifact:
- `reports/runs/strict_e2e_validation.json`

### Milestone signoff (single command)
```bash
python scripts/milestone_signoff.py projects/overnight-e2e-01
```

Run signoff with an auto fresh strict cycle before validation:
```bash
python scripts/milestone_signoff.py projects/overnight-e2e-01 --rerun
```

Fast debug cycle (short rerun budget):
```bash
python scripts/milestone_signoff.py projects/overnight-e2e-01 --rerun --max-steps 30
```

Validate a specific historical run id:
```bash
python scripts/milestone_signoff.py projects/overnight-e2e-01 --run-id run_2026-02-27T15-32-00Z_072684
```

Output artifacts:
- `reports/runs/milestone_signoff.json`
- `reports/runs/milestone_signoff.md`

Note: the signoff wrapper auto-refreshes `reports/runs/latest_run_report.json` for the target project before validation to avoid stale report mismatch failures.

⚠️ Report freshness policy:
- Treat `scripts/milestone_signoff.py` as the canonical report path for milestone decisions.
- Avoid manual/direct edits to `reports/runs/latest_run_report.json`.
- Use wrapper commands to prevent stale evidence acceptance.

### Strict E2E convergence debug harness
Run one strict cycle and capture route trace:
```bash
python scripts/run_strict_e2e_cycle.py --project-dir projects/overnight-e2e-01 --max-steps 120
```

Compare two trace files:
```bash
python scripts/route_diff_report.py --base reports/runs/strict_e2e_cycle_A.json --head reports/runs/strict_e2e_cycle_B.json
```

## 📜 Logs
Check `sweat.log` for detailed execution traces.
