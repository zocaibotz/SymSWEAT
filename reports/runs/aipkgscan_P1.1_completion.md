# P1.1: AST-Backed Dataflow Slicing

## Status: Completed

1. **Added `esprima` dependency** (`pyproject.toml`):
   - Added `esprima>=4.0.1` to the core dependencies.

2. **Created `dataflow_slicer.py`** (`src/aipkgscan/taint/dataflow_slicer.py`):
   - Full AST traversal using esprima's `parseScript()` on JavaScript/TypeScript files.
   - **Source identification**: `process.env.SECRET*`, `/etc/passwd`, `os.homedir()`, etc. via pattern matching on MemberExpression chains.
   - **Sink classification**: `eval`, `new Function`, `child_process.exec/spawn/fork`, `fetch`, `fs.readFile*`, and more — classified by callee chain analysis.
   - **Interprocedural taint propagation**: Variable assignments (`const b = a`) inherit taint from their source identifier.
   - **Deep nested object traversal**: `collect_tainted()` recursively finds tainted identifiers buried in object/array structures (e.g., `{ headers: { Authorization: secret } }`).
   - **NewExpression support**: `new Function(...)` is handled as a `Function` sink.
   - **Malformed JS fallback**: Any parse error is silently caught and returns no slices rather than crashing.
   - File size limit: only AST-parses files under 50KB.

3. **Integrated into `PackageAnalyzer`** (`analyzer.py`):
   - `DataflowSlicer` is instantiated alongside `TaintSliceBuilder`.
   - `slice_package()` is run on the package and its slices are merged into the existing slice collection.
   - Dataflow slices take precedence (first-found, deduplicated by ID).

4. **Updated `taint/__init__.py`**:
   - Exports `DataflowSlicer` and `DataflowResult` alongside existing classes.

5. **Tests** (`tests/test_dataflow.py`):
   - 14 new tests covering:
     - TaintEnv basic operations
     - `eval(something_from_env)` chain detection
     - `new Function(sink)` detection
     - `child_process.exec(fs_read)` chain detection
     - `fetch(...)` with nested object taint
     - Variable alias propagation (`const b = a; eval(b)`)
     - Empty / benign / malformed code handling
     - Node/edge/summary population

## Validation:
- All 124 `pytest` tests pass successfully (110 existing + 14 new).
- Modifications preserve existing behavior and integrate cleanly.

## SWEAT Integration:
- Changes committed to `aipkgscan` origin's `main` branch and pushed.
- This report signifies completion of task P1.1.