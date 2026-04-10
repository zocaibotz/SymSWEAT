#!/usr/bin/env python3
from src.sweat_v2.shadow_diagnostics import write_disagreement_report


if __name__ == "__main__":
    payload = write_disagreement_report()
    print("reports/runs/v2_shadow_disagreements.json")
    print(f"disagreed={payload['disagreed']}")
