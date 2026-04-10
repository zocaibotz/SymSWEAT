#!/usr/bin/env python3
from src.tools.security_remediation import get_security_remediation_engine
import json


def main():
    plan = get_security_remediation_engine().build_plan()
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
