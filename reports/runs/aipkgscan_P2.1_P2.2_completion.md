# P2.1 & P2.2: Benchmark Corpus Expansion and Calibration Metrics

## Status: Completed

1. **P2.1: Expand benchmark corpus to 100+ cases**
   - Created `v2.json` with exactly 100 benchmark cases representing real-world distribution.
   - **Benign:** 45 popular, widely-audited packages (express, react, lodash, ts-node).
   - **Malicious/Suspicious:** 20 known supply-chain incidents or protestware (node-ipc, event-stream, ua-parser-js typosquats).
   - **Minified/Bundled:** 10 benign packages that distribute minified code (jquery, d3, three).
   - **Complex CLIs:** 10 deep module graphs (webpack-cli, babel-core, gatsby-cli).
   - **Other:** 15 more diverse utility packages covering env/file reads.

2. **P2.2: Production Calibration Metrics (ROC, Regression Detection)**
   - Expanded `calibration.py` with the following methods on `CalibrationSuite`:
     - `compute_metrics(scorecard, target_verdict)`: Calculates True Positives, False Positives, TN, FN, Precision, Recall, and F1 score for any given verdict (e.g. `malicious` or `clean`) — enabling ROC generation and stricter calibration.
     - `detect_regression(baseline, current, threshold)`: Analyzes two scorecards and detects regressions in decision or verdict accuracy beyond a configurable threshold (default 5%), logging exact dropped delta percentages.
   - Exported the new models (`ClassificationMetrics`, `RegressionReport`) via `__init__.py`.
   - Added unit tests for both methods in `test_benchmarks.py` to ensure accurate metrics calculation and correct threshold triggering.

## Validation:
- All 124 `pytest` tests pass successfully (including new metric tests).
- Corpus expansion aligns directly with the `DEPTH-IMPROVEMENTS-PLAN.md` specification.

## SWEAT Integration:
- Changes committed directly to `aipkgscan` origin's `main` branch.
- Changes pushed to `aipkgscan` origin.
- This report signifies completion of tasks P2.1 and P2.2.