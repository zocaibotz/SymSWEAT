# P2.3: LLM Prompt Optimization & Token Accounting

## Status: Completed

1. **Token Accounting Added**:
   - Extended `AnalysisResult` in `src/aipkgscan/llm/base.py` to include `prompt_tokens`, `completion_tokens`, and `total_tokens`.
   - Updated `OpenAICompatibleProvider` in `src/aipkgscan/llm/providers.py` to extract `usage` tokens from the HTTP API response and populate `AnalysisResult`.
   
2. **Context Capping Logic & CLI Flag**:
   - Added `--max-context-tokens` CLI option (default: `100000`) in `src/aipkgscan/ecosystems/npm.py` (`scan` and `install` commands).
   - Plumbed `max_context_tokens` into `PackageAnalyzer` initialization.
   - Updated `_collect_source_code` in `src/aipkgscan/analyzer.py` to calculate a hard character cap (`max_chars = max_context_tokens * 4`).
   - If the raw source code string exceeds this cap, it truncates the middle using `...[truncated for context token limits]...`.
   
3. **Benchmark Harness Updates**:
   - Updated `BenchmarkResult` and `BenchmarkScorecard` in `src/aipkgscan/benchmarks/harness.py` to track token metrics.
   - Summed up tokens used across all test cases.

4. **Security Report Updates**:
   - Plumbed token metrics into `SecurityReport` via `report.py`.
   - Included token usage stats in the emitted JSON output.

## Validation:
- All 110 `pytest` tests pass successfully.
- Modifications adhere to existing architecture.

## SWEAT Integration:
- Changes were committed directly to `aipkgscan` repository on the `main` branch.
- Changes were pushed to `aipkgscan` origin.
- This report signifies the completion of task P2.3.