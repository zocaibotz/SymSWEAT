#!/usr/bin/env python3
from src.sweat_v2.shadow_weekly import write_weekly_report


if __name__ == "__main__":
    payload = write_weekly_report()
    print("reports/runs/v2_shadow_weekly_report.json")
    print(f"agreement_rate={payload['agreement_rate']:.4f}")
