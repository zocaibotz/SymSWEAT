#!/bin/bash
# validate_artifacts.sh
# Usage: ./validate_artifacts.sh <ticket_type> <issue_identifier> <commits_ahead>

set -euo pipefail

TICKET_TYPE=${1:-implementation}
ISSUE_IDENTIFIER=${2:-}
COMMITS_AHEAD=${3:-0}
DEFAULT_BRANCH=${VALIDATION_DEFAULT_BRANCH:-main}
AGENT_SEMANTIC_REASON=${AGENT_SEMANTIC_REASON:-}

MISSING=()
PLACEHOLDER_ONLY_FILES=()
MEANINGFUL_CHANGED_FILES=()
CHANGED_FILES=()

is_placeholder_file() {
  case "$1" in
    "docs/spec/${ISSUE_IDENTIFIER}.md"|"docs/architecture/SYSTEM_DESIGN.md"|"docs/architecture/API_CONTRACTS.md"|"reports/security_scan.txt"|"swarm_prompt.txt")
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

# Base requirements for all profiles
if [ ! -s "reports/security_scan.txt" ]; then
  MISSING+=("reports/security_scan.txt")
fi

if [ ! -f "docs/spec/${ISSUE_IDENTIFIER}.md" ]; then
  MISSING+=("docs/spec/${ISSUE_IDENTIFIER}.md")
fi

if [ "$TICKET_TYPE" = "architect" ]; then
  if [ ! -f "docs/architecture/SYSTEM_DESIGN.md" ]; then
    MISSING+=("docs/architecture/SYSTEM_DESIGN.md")
  fi
  if [ ! -f "docs/architecture/API_CONTRACTS.md" ]; then
    MISSING+=("docs/architecture/API_CONTRACTS.md")
  fi
elif [ "$TICKET_TYPE" = "test" ]; then
  :
fi

BASE_REF="origin/$DEFAULT_BRANCH"
if git rev-parse --verify --quiet "$BASE_REF" >/dev/null 2>&1; then
  BASE_SHA="$(git merge-base HEAD "$BASE_REF" 2>/dev/null || true)"
  if [ -z "$BASE_SHA" ]; then
    BASE_SHA="$BASE_REF"
  fi
  while IFS= read -r path; do
    [ -n "$path" ] || continue
    CHANGED_FILES+=("$path")
    if is_placeholder_file "$path"; then
      PLACEHOLDER_ONLY_FILES+=("$path")
    else
      MEANINGFUL_CHANGED_FILES+=("$path")
    fi
  done < <(git diff --name-only "$BASE_SHA..HEAD" 2>/dev/null || true)
fi

VALID="true"
REASON=""
PLACEHOLDER_ONLY="false"
STATUS_ONLY_SIGNAL="false"

if [ -n "$AGENT_SEMANTIC_REASON" ]; then
  VALID="false"
  REASON="$AGENT_SEMANTIC_REASON"
  STATUS_ONLY_SIGNAL="true"
elif [ ${#MISSING[@]} -gt 0 ]; then
  VALID="false"
  REASON="missing_artifacts"
elif [ "$COMMITS_AHEAD" -eq 0 ]; then
  VALID="false"
  REASON="no_commits"
elif [ ${#CHANGED_FILES[@]} -gt 0 ] && [ ${#MEANINGFUL_CHANGED_FILES[@]} -eq 0 ]; then
  VALID="false"
  REASON="placeholder_only_changes"
  PLACEHOLDER_ONLY="true"
fi

if [ ${#MISSING[@]} -eq 0 ]; then
  MISSING_JSON='[]'
else
  MISSING_JSON=$(printf '%s\n' "${MISSING[@]}" | jq -R . | jq -s .)
fi

if [ ${#CHANGED_FILES[@]} -eq 0 ]; then
  CHANGED_JSON='[]'
else
  CHANGED_JSON=$(printf '%s\n' "${CHANGED_FILES[@]}" | jq -R . | jq -s .)
fi

if [ ${#MEANINGFUL_CHANGED_FILES[@]} -eq 0 ]; then
  MEANINGFUL_JSON='[]'
else
  MEANINGFUL_JSON=$(printf '%s\n' "${MEANINGFUL_CHANGED_FILES[@]}" | jq -R . | jq -s .)
fi

if [ ${#PLACEHOLDER_ONLY_FILES[@]} -eq 0 ]; then
  PLACEHOLDER_JSON='[]'
else
  PLACEHOLDER_JSON=$(printf '%s\n' "${PLACEHOLDER_ONLY_FILES[@]}" | jq -R . | jq -s .)
fi

jq -n \
  --arg valid "$VALID" \
  --arg reason "$REASON" \
  --arg commits "$COMMITS_AHEAD" \
  --argjson missing "$MISSING_JSON" \
  --argjson changed "$CHANGED_JSON" \
  --argjson meaningful "$MEANINGFUL_JSON" \
  --argjson placeholder "$PLACEHOLDER_JSON" \
  --arg placeholder_only "$PLACEHOLDER_ONLY" \
  --arg status_only_signal "$STATUS_ONLY_SIGNAL" \
  --arg agent_semantic_reason "$AGENT_SEMANTIC_REASON" \
  '{
    valid: ($valid == "true"),
    reason: $reason,
    commits_ahead: ($commits|tonumber),
    missing_artifacts: $missing,
    changed_files: $changed,
    meaningful_changed_files: $meaningful,
    placeholder_only_files: $placeholder,
    placeholder_only: ($placeholder_only == "true"),
    status_only_signal: ($status_only_signal == "true"),
    agent_semantic_reason: $agent_semantic_reason
  }'
