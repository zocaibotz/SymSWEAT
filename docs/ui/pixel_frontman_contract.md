# Pixel → Frontman Contract

_Last updated: 2026-02-23 UTC_

## Pixel output schema (`docs/ux/package.json`)

```json
{
  "personas": [{"name": "...", "goals": ["..."]}],
  "user_journey": ["step 1", "step 2"],
  "screens": [{"name": "Home", "elements": ["..."]}],
  "style_tokens": {"primary": "#111827", "spacing": {"md": 16}}
}
```

### Required fields
- `personas` (array)
- `user_journey` (array)
- `screens` (array)
- `style_tokens` (object)

## Frontman expected output

Frontman must return **only** this JSON tool-call shape:

```json
{
  "tool": "write_file",
  "args": {
    "path": "src/App.jsx",
    "content": "...React code..."
  }
}
```

### Rules
- `path` must be inside `src/`
- file extension must be `.jsx` or `.tsx`
- `content` should define `export default function App()`

## Handoff artifact
Frontman writes `docs/ui/handoff_contract.json` with:
- source UX package path
- generated UI file path
- props contract
- style token source reference

<!-- DOC_SYNC: 2026-02-24 -->
