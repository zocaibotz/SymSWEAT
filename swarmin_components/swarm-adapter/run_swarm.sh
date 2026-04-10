#!/bin/bash
# SWARM Adapter for Symphony
# Triggered by the Symphony Poller with environment variables:
# ISSUE_ID, ISSUE_IDENTIFIER, ISSUE_TITLE, ISSUE_DESCRIPTION, REPO_URL

set -euo pipefail

WORKSPACE_ROOT="${WORKSPACE_ROOT:-/home/claw-admin/.openclaw/workspace/projects/symphony}"
RUNS_DIR="$WORKSPACE_ROOT/runs"
ACTIVE_RUNS_DIR="$RUNS_DIR/active"
ATTEMPT_RUNS_DIR="$RUNS_DIR/attempts"
ISSUE_RUNS_DIR="$RUNS_DIR/issues"
SWARM_ATTEMPT_ID="${SWARM_ATTEMPT_ID:-$(date -u +%Y%m%dT%H%M%S%NZ)}"
CWD="$WORKSPACE_ROOT/$ISSUE_IDENTIFIER"
REPO_WORKDIR="$CWD/repo"
LOG_FILE="$CWD/adapter_log.txt"
AGENT_OUTPUT_FILE="$CWD/agent_output.txt"
RUN_LEDGER="$ATTEMPT_RUNS_DIR/${ISSUE_IDENTIFIER}--${SWARM_ATTEMPT_ID}.json"
ISSUE_SUMMARY_LEDGER="$ISSUE_RUNS_DIR/${ISSUE_IDENTIFIER}.json"
LEGACY_RUN_LEDGER="$RUNS_DIR/${ISSUE_IDENTIFIER}.json"
ACTIVE_ATTEMPT_REGISTRY="$ACTIVE_RUNS_DIR/${ISSUE_IDENTIFIER}--${SWARM_ATTEMPT_ID}.json"
ACTIVE_CURRENT_REGISTRY="$ACTIVE_RUNS_DIR/${ISSUE_IDENTIFIER}.current.json"
VALIDATION_SCRIPT="${VALIDATION_SCRIPT:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/validate_artifacts.sh}"

START_TS="$(date -u +%FT%TZ)"
PR_URL=""
COMMITS_AHEAD=0
CHANGED_FILES=0
VALIDATION_JSON='{}'
FINAL_STATUS="failed"
FINAL_REASON="unknown"
TICKET_TYPE="implementation"
REPO_PATH=""
DEFAULT_BRANCH=""
AGENT_EXIT=0
AGENT_SEMANTIC_REASON=""
HEARTBEAT_INTERVAL_SEC="${HEARTBEAT_INTERVAL_SEC:-60}"
CURRENT_PHASE="adapter_bootstrap"
PHASE_STARTED_AT="$START_TS"
LAST_HEARTBEAT_TS="$START_TS"
LAST_EVENT="adapter_started"
AUTO_REVIEW_ENABLED="${AUTO_REVIEW_ENABLED:-false}"
AUTO_MERGE_ON_APPROVE="${AUTO_MERGE_ON_APPROVE:-false}"
REVIEWER_AGENT="${REVIEWER_AGENT:-main}"
REVIEW_TIMEOUT_SEC="${REVIEW_TIMEOUT_SEC:-180}"

mkdir -p "$CWD" "$RUNS_DIR" "$ACTIVE_RUNS_DIR" "$ATTEMPT_RUNS_DIR" "$ISSUE_RUNS_DIR"
cd "$CWD"

echo "Running SWARM Adapter for $ISSUE_IDENTIFIER" > "$LOG_FILE"

log() {
  echo "$1" >> "$LOG_FILE"
}

classify_agent_output() {
  local output_file="$1"
  [ -f "$output_file" ] || return 1

  local lowered
  lowered="$(tr '[:upper:]' '[:lower:]' < "$output_file")"

  if printf '%s' "$lowered" | grep -Eq "can't start|cannot start|can not start|concurrency limit|concurrency-limited|queued|queueing|refused|refusal|busy right now|too many active|subagent concurrency limit"; then
    echo "agent_status_only"
    return 0
  fi

  if printf '%s' "$lowered" | grep -Eq "(^|[^a-z])(started|launch(ed)?|spawn(ed)?)([^a-z]|$)" \
     && ! printf '%s' "$lowered" | grep -Eq "pull request|pr url|tests? passed|implemented|created file|updated file|committed|validation envelope"; then
    echo "agent_launch_only"
    return 0
  fi

  return 1
}

update_active_registry() {
  local status="${1:-}"
  local registry_path="$ACTIVE_ATTEMPT_REGISTRY"
  local current_path="$ACTIVE_CURRENT_REGISTRY"
  local tmp_attempt tmp_current

  [ -n "${ISSUE_IDENTIFIER:-}" ] || return 0
  [ -n "${SWARM_ATTEMPT_ID:-}" ] || return 0

  tmp_attempt="${registry_path}.tmp"
  jq -n \
    --arg issue_id "${ISSUE_ID:-}" \
    --arg issue_identifier "${ISSUE_IDENTIFIER:-}" \
    --arg attempt_id "$SWARM_ATTEMPT_ID" \
    --arg status "${status:-running}" \
    --arg poller_dispatch_ts "$(jq -r '.poller_dispatch_ts // empty' "$registry_path" 2>/dev/null || true)" \
    --arg last_heartbeat_ts "$LAST_HEARTBEAT_TS" \
    --arg current_phase "$CURRENT_PHASE" \
    --arg phase_started_at "$PHASE_STARTED_AT" \
    --arg last_event "$LAST_EVENT" \
    --arg ledger_path "$RUN_LEDGER" \
    --arg issue_summary_path "$ISSUE_SUMMARY_LEDGER" \
    --arg branch "${ISSUE_IDENTIFIER:-}" \
    --arg registry_path "$registry_path" \
    --arg current_path "$current_path" \
    --argjson adapter_pid "$(jq -r '.adapter_pid // 0' "$registry_path" 2>/dev/null || echo 0)" \
    '{
      issue_id:$issue_id,
      issue_identifier:$issue_identifier,
      attempt_id:$attempt_id,
      status:$status,
      poller_dispatch_ts:(if ($poller_dispatch_ts|length) > 0 then $poller_dispatch_ts else $last_heartbeat_ts end),
      last_heartbeat_ts:$last_heartbeat_ts,
      current_phase:$current_phase,
      phase_started_at:$phase_started_at,
      last_event:$last_event,
      ledger_path:$ledger_path,
      issue_summary_path:$issue_summary_path,
      branch:$branch,
      adapter_pid:(if $adapter_pid == 0 then null else $adapter_pid end),
      registry_path:$registry_path,
      current_path:$current_path
    }' > "$tmp_attempt"
  mv "$tmp_attempt" "$registry_path"

  tmp_current="${current_path}.tmp"
  jq '{
      issue_id,
      issue_identifier,
      attempt_id,
      status,
      poller_dispatch_ts,
      last_heartbeat_ts,
      current_phase,
      phase_started_at,
      last_event,
      ledger_path,
      issue_summary_path,
      branch,
      adapter_pid,
      registry_path,
      current_path
    }' "$registry_path" > "$tmp_current"
  mv "$tmp_current" "$current_path"
}

heartbeat() {
  local phase="$1"
  local event="$2"
  local status="${3:-running}"
  local now
  now="$(date -u +%FT%TZ)"

  if [ "$CURRENT_PHASE" != "$phase" ]; then
    CURRENT_PHASE="$phase"
    PHASE_STARTED_AT="$now"
  fi

  LAST_HEARTBEAT_TS="$now"
  LAST_EVENT="$event"

  if [ -f "$RUN_LEDGER" ]; then
    local tmp_ledger
    tmp_ledger="${RUN_LEDGER}.tmp"
    jq \
      --arg status "$status" \
      --arg last_heartbeat_ts "$LAST_HEARTBEAT_TS" \
      --arg current_phase "$CURRENT_PHASE" \
      --arg phase_started_at "$PHASE_STARTED_AT" \
      --arg last_event "$LAST_EVENT" \
      '.status=$status
       | .last_heartbeat_ts=$last_heartbeat_ts
       | .current_phase=$current_phase
       | .phase_started_at=$phase_started_at
       | .last_event=$last_event' "$RUN_LEDGER" > "$tmp_ledger" && mv "$tmp_ledger" "$RUN_LEDGER"
      cp "$RUN_LEDGER" "$LEGACY_RUN_LEDGER" 2>/dev/null || true
  fi

  update_active_registry "$status"
}

heartbeat_loop() {
  local pid="$1"
  local phase="$2"
  local label="$3"

  while kill -0 "$pid" 2>/dev/null; do
    sleep "$HEARTBEAT_INTERVAL_SEC"
    kill -0 "$pid" 2>/dev/null || break
    heartbeat "$phase" "${label}:heartbeat" "running"
  done
}

run_with_timeout() {
  local label="$1"
  local timeout_sec="$2"
  shift 2

  local phase="${RUN_HEARTBEAT_PHASE:-$label}"
  log "Starting: $label (timeout=${timeout_sec}s)"
  heartbeat "$phase" "${label}:start" "running"

  timeout --kill-after=15s "$timeout_sec" "$@" &
  local cmd_pid=$!
  heartbeat_loop "$cmd_pid" "$phase" "$label" &
  local hb_pid=$!

  local exit_code=0
  wait "$cmd_pid" || exit_code=$?

  kill "$hb_pid" 2>/dev/null || true
  wait "$hb_pid" 2>/dev/null || true

  if [ "$exit_code" -eq 0 ]; then
    log "Finished: $label"
    heartbeat "$phase" "${label}:end" "running"
    return 0
  fi

  log "Failed: $label (exit=$exit_code)"
  heartbeat "$phase" "${label}:failed" "running"
  return "$exit_code"
}

write_ledger() {
  local status="$1"
  local reason="$2"
  local ended_at
  local tmp_summary
  local prior_summary_source
  ended_at="$(date -u +%FT%TZ)"

  LAST_HEARTBEAT_TS="$ended_at"
  LAST_EVENT="ledger:${status}"

  jq -n \
    --arg issue_id "${ISSUE_ID:-}" \
    --arg issue_identifier "${ISSUE_IDENTIFIER:-}" \
    --arg issue_title "${ISSUE_TITLE:-}" \
    --arg attempt_id "$SWARM_ATTEMPT_ID" \
    --arg ticket_type "$TICKET_TYPE" \
    --arg repo_url "${REPO_URL:-}" \
    --arg repo_path "$REPO_PATH" \
    --arg status "$status" \
    --arg reason "$reason" \
    --arg pr_url "$PR_URL" \
    --arg started_at "$START_TS" \
    --arg ended_at "$ended_at" \
    --arg last_heartbeat_ts "$LAST_HEARTBEAT_TS" \
    --arg current_phase "$CURRENT_PHASE" \
    --arg phase_started_at "$PHASE_STARTED_AT" \
    --arg last_event "$LAST_EVENT" \
    --arg commits_ahead "$COMMITS_AHEAD" \
    --arg changed_files "$CHANGED_FILES" \
    --arg ledger_path "$RUN_LEDGER" \
    --arg issue_summary_path "$ISSUE_SUMMARY_LEDGER" \
    --argjson validation "$VALIDATION_JSON" \
    '{
      issue_id:$issue_id,
      issue_identifier:$issue_identifier,
      issue_title:$issue_title,
      attempt_id:$attempt_id,
      ticket_type:$ticket_type,
      repo_url:$repo_url,
      repo_path:$repo_path,
      status:$status,
      reason:$reason,
      pr_url:$pr_url,
      started_at:$started_at,
      ended_at:$ended_at,
      last_heartbeat_ts:$last_heartbeat_ts,
      current_phase:$current_phase,
      phase_started_at:$phase_started_at,
      last_event:$last_event,
      commits_ahead: ($commits_ahead|tonumber),
      changed_files: ($changed_files|tonumber),
      ledger_path:$ledger_path,
      issue_summary_path:$issue_summary_path,
      validation:$validation
    }' > "$RUN_LEDGER"

  tmp_summary="${ISSUE_SUMMARY_LEDGER}.tmp"
  prior_summary_source="$ISSUE_SUMMARY_LEDGER"
  if [ ! -f "$prior_summary_source" ]; then
    prior_summary_source=/dev/null
  fi
  jq -n \
    --arg issue_id "${ISSUE_ID:-}" \
    --arg issue_identifier "${ISSUE_IDENTIFIER:-}" \
    --arg issue_title "${ISSUE_TITLE:-}" \
    --arg attempt_id "$SWARM_ATTEMPT_ID" \
    --arg status "$status" \
    --arg reason "$reason" \
    --arg started_at "$START_TS" \
    --arg ended_at "$ended_at" \
    --arg latest_ledger_path "$RUN_LEDGER" \
    --slurpfile prior "$prior_summary_source" \
    '
      def prior_obj: ($prior[0] // {});
      def prior_attempts: (prior_obj.attempts // []);
      {
        issue_id:$issue_id,
        issue_identifier:$issue_identifier,
        issue_title:$issue_title,
        latest_attempt_id:$attempt_id,
        latest_status:$status,
        latest_reason:$reason,
        latest_started_at:$started_at,
        latest_ended_at:$ended_at,
        latest_ledger_path:$latest_ledger_path,
        attempts:(
          prior_attempts
          + [{
              attempt_id:$attempt_id,
              status:$status,
              reason:$reason,
              started_at:$started_at,
              ended_at:$ended_at,
              ledger_path:$latest_ledger_path
            }]
          | unique_by(.attempt_id)
          | sort_by(.started_at // .ended_at // "")
        )
      }
    ' > "$tmp_summary"
  mv "$tmp_summary" "$ISSUE_SUMMARY_LEDGER"

  # Temporary compatibility mirror for older operators/scripts still reading the legacy per-issue path.
  cp "$RUN_LEDGER" "$LEGACY_RUN_LEDGER"
  update_active_registry "$status"
}

linear_comment() {
  local body="$1"
  [ -n "${LINEAR_API_KEY:-}" ] || return 0
  [ -n "${ISSUE_ID:-}" ] || return 0

  local mutation payload
  mutation='mutation CommentCreate($issueId: String!, $body: String!) { commentCreate(input: { issueId: $issueId, body: $body }) { success } }'
  payload=$(jq -n --arg query "$mutation" --arg issueId "$ISSUE_ID" --arg body "$body" '{query:$query, variables:{issueId:$issueId, body:$body}}')

  curl -s -X POST https://api.linear.app/graphql \
    -H "Authorization: $LINEAR_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$payload" >> "$LOG_FILE" 2>&1 || log "Linear comment failed"
}

linear_transition() {
  local preferred_csv="$1" # e.g. "In Review,Review,Done"
  [ -n "${LINEAR_API_KEY:-}" ] || return 0
  [ -n "${ISSUE_ID:-}" ] || return 0

  local states_payload states_json payload state_name state_id success
  states_payload=$(jq -n --arg issueId "$ISSUE_ID" '{query:"query TeamStates($issueId: String!) { issue(id:$issueId){ team { id states { nodes { id name type } } } } }", variables:{issueId:$issueId}}')
  states_json=$(curl -s -X POST https://api.linear.app/graphql \
    -H "Authorization: $LINEAR_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$states_payload" 2>> "$LOG_FILE" || true)

  state_id=""
  IFS=',' read -ra candidates <<< "$preferred_csv"
  for state_name in "${candidates[@]}"; do
    state_name="$(echo "$state_name" | xargs)"
    state_id=$(echo "$states_json" | jq -r --arg n "$state_name" '.data.issue.team.states.nodes[]? | select(.name==$n) | .id' | head -n1)
    if [ -n "$state_id" ] && [ "$state_id" != "null" ]; then
      break
    fi
  done

  # Fallback: if success path asked for done/review but exact names missing, choose any completed state for this team.
  if [ -z "$state_id" ] || [ "$state_id" = "null" ]; then
    if echo "$preferred_csv" | grep -Eqi 'done|review'; then
      state_id=$(echo "$states_json" | jq -r '.data.issue.team.states.nodes[]? | select((.type // "")|ascii_downcase == "completed") | .id' | head -n1)
    fi
  fi

  if [ -z "$state_id" ] || [ "$state_id" = "null" ]; then
    log "None of preferred/team states found: $preferred_csv"
    return 0
  fi

  payload=$(jq -n \
    --arg query 'mutation UpdateIssue($id: String!, $stateId: String!) { issueUpdate(id: $id, input: { stateId: $stateId }) { success } }' \
    --arg id "$ISSUE_ID" \
    --arg stateId "$state_id" \
    '{query:$query, variables:{id:$id, stateId:$stateId}}')

  success=$(curl -s -X POST https://api.linear.app/graphql \
    -H "Authorization: $LINEAR_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$payload" 2>> "$LOG_FILE" | jq -r '.data.issueUpdate.success // "false"')

  if [ "$success" != "true" ]; then
    log "Linear state transition returned success=false for issue $ISSUE_ID"
  fi
}

auto_reviewer_verdict() {
  local pr_url="$1"
  local review_out
  review_out=$(run_with_timeout "reviewer agent" "$REVIEW_TIMEOUT_SEC" openclaw agent --agent "$REVIEWER_AGENT" --message "Review this PR for correctness, safety, and completeness. PR: $pr_url . Respond with first line exactly APPROVE or REJECT, then concise rationale." 2>>"$LOG_FILE" || true)
  printf "%s" "$review_out" >> "$LOG_FILE"
  printf "\n" >> "$LOG_FILE"
  if echo "$review_out" | head -n1 | grep -Eq '^APPROVE\b'; then
    echo "APPROVE"
  else
    echo "REJECT"
  fi
}

# Ticket type profile
if echo "${ISSUE_TITLE:-}" | grep -qi "architect"; then
  TICKET_TYPE="architect"
elif echo "${ISSUE_TITLE:-}" | grep -Eqi "test|testing|integration"; then
  TICKET_TYPE="test"
fi

write_ledger "started" "dispatch"
heartbeat "adapter_bootstrap" "ledger_initialized" "running"

# 1) Clone + branch
if [ -z "${REPO_URL:-}" ]; then
  FINAL_REASON="missing_repo_url"
  log "Missing REPO_URL"
  write_ledger "failed" "$FINAL_REASON"
  linear_comment "**SWARM Execution Incomplete**\n\nNo repo URL resolved for '$ISSUE_IDENTIFIER'."
  linear_transition "Blocked,Backlog,Todo"
  exit 10
fi

log "Cloning repository: $REPO_URL"
REPO_PATH=$(echo "$REPO_URL" | sed 's|https://github.com/||' | sed 's|.git$||')
rm -rf "$REPO_WORKDIR"
if RUN_HEARTBEAT_PHASE="clone" run_with_timeout "gh repo clone" "${CLONE_TIMEOUT_SEC:-180}" gh repo clone "$REPO_PATH" "$REPO_WORKDIR" 2>> "$LOG_FILE"; then
  :
else
  FINAL_REASON="clone_failed"
  write_ledger "failed" "$FINAL_REASON"
  linear_transition "Blocked,Backlog,Todo"
  exit 11
fi
cd "$REPO_WORKDIR"
heartbeat "branch_setup" "repo_cloned" "running"

# Ensure commits work in fresh ephemeral clones without overriding existing identity.
ensure_git_identity() {
  local git_name git_email

  git_name="$(git config --get user.name || true)"
  git_email="$(git config --get user.email || true)"

  if [ -z "$git_name" ]; then
    git_name="${SWARM_GIT_AUTHOR_NAME:-SWARM Bot}"
    git config --local user.name "$git_name"
    log "Configured repo-local git user.name: $git_name"
  fi

  if [ -z "$git_email" ]; then
    git_email="${SWARM_GIT_AUTHOR_EMAIL:-swarm-bot@localhost}"
    git config --local user.email "$git_email"
    log "Configured repo-local git user.email: $git_email"
  fi

  # Configure git credential helper so push works without interactive prompt
  if [ -n "${GH_TOKEN:-}" ]; then
    # Use store helper with a credentials file - more portable than bash function
    git config --local credential.useHttpPath false
    printf '%s\n' "https://x-access-token:${GH_TOKEN}@github.com" > "$(git config --get user.home 2>/dev/null || echo "$HOME")/.git-credentials"
    git config --local credential.helper 'store'
    log "Configured git credential helper for push"
  fi

  export GIT_AUTHOR_NAME="${GIT_AUTHOR_NAME:-$(git config --get user.name)}"
  export GIT_AUTHOR_EMAIL="${GIT_AUTHOR_EMAIL:-$(git config --get user.email)}"
  export GIT_COMMITTER_NAME="${GIT_COMMITTER_NAME:-$GIT_AUTHOR_NAME}"
  export GIT_COMMITTER_EMAIL="${GIT_COMMITTER_EMAIL:-$GIT_AUTHOR_EMAIL}"
}

ensure_git_identity

RUN_HEARTBEAT_PHASE="branch_setup" run_with_timeout "git fetch origin" "${GIT_TIMEOUT_SEC:-120}" git fetch origin 2>> "$LOG_FILE" || true
DEFAULT_BRANCH=$(git remote show origin 2>> "$LOG_FILE" | sed -n '/HEAD branch/s/.*: //p' | head -n1)
if [ -z "$DEFAULT_BRANCH" ]; then
  DEFAULT_BRANCH="main"
fi
if ! git show-ref --verify --quiet "refs/remotes/origin/$DEFAULT_BRANCH"; then
  FINAL_REASON="default_branch_missing"
  log "Default branch origin/$DEFAULT_BRANCH not found"
  write_ledger "failed" "$FINAL_REASON"
  linear_comment "**SWARM Execution Incomplete**\n\nMissing remote default branch origin/$DEFAULT_BRANCH for '$ISSUE_IDENTIFIER'."
  linear_transition "Blocked,Backlog,Todo"
  exit 12
fi
if RUN_HEARTBEAT_PHASE="branch_setup" run_with_timeout "git checkout branch" "${GIT_TIMEOUT_SEC:-120}" git checkout -B "$ISSUE_IDENTIFIER" "origin/$DEFAULT_BRANCH" 2>> "$LOG_FILE"; then
  :
else
  RUN_HEARTBEAT_PHASE="branch_setup" run_with_timeout "git checkout branch fallback" "${GIT_TIMEOUT_SEC:-120}" git checkout -B "$ISSUE_IDENTIFIER" 2>> "$LOG_FILE"
fi
log "Created branch from origin/$DEFAULT_BRANCH: $ISSUE_IDENTIFIER"
heartbeat "branch_setup" "branch_ready" "running"

# 2) Prompt
cat <<EOF > swarm_prompt.txt
Run swarm:
Requirement: $ISSUE_TITLE - $ISSUE_DESCRIPTION
Mode: build
Constraints:
  - MANDATORY PIPELINE: SDD -> TDD -> Implement -> Security Scan -> Critic Review.
  - PLANNER: MUST generate \`docs/spec/${ISSUE_IDENTIFIER}.md\`.
  - CODER: MUST write failing tests first (Red), then passing tests (Green), with test logs in output.
  - SECURITY: MUST run local SAST/dependency checks and output \`reports/security_scan.txt\`; remediate High/Critical findings.
  - CWD: Strictly locked to $REPO_WORKDIR.
  - EXECUTION DISCIPLINE: Do the actual file edits first. Do NOT return status-only messages like "started"/"launched" without producing artifacts.
Hard Output Contract (required before completion):
  1) \`docs/spec/${ISSUE_IDENTIFIER}.md\`
  2) \`reports/security_scan.txt\`
  3) For Architect tickets: \`docs/architecture/SYSTEM_DESIGN.md\` and \`docs/architecture/API_CONTRACTS.md\`
  4) Git commits on branch \`$ISSUE_IDENTIFIER\`
  5) PR creation via \`gh pr create\` and PR URL
  - If unable to satisfy all required outputs, STOP and return explicit failure reason.
EOF

log "Generated SWARM prompt in $REPO_WORKDIR/swarm_prompt.txt"

# 3) Execute agent (timeout to avoid hangs)
AGENT_TIMEOUT_SEC="${AGENT_TIMEOUT_SEC:-420}"
: > "$AGENT_OUTPUT_FILE"

EXECUTOR="${AGENT_EXECUTOR_CMD:-openclaw agent --agent main --message}"

log "Triggering SWARM via executor: $EXECUTOR (timeout=${AGENT_TIMEOUT_SEC}s)"
if RUN_HEARTBEAT_PHASE="agent_invoke" run_with_timeout "agent_invoke" "$AGENT_TIMEOUT_SEC" sh -c 'eval "$0" < "$1"' "$EXECUTOR" "$REPO_WORKDIR/swarm_prompt.txt" > "$AGENT_OUTPUT_FILE" 2>&1; then
  cat "$AGENT_OUTPUT_FILE" >> "$LOG_FILE"
  printf '\n' >> "$LOG_FILE"
else
  AGENT_EXIT=$?
  cat "$AGENT_OUTPUT_FILE" >> "$LOG_FILE" 2>/dev/null || true
  printf '\n' >> "$LOG_FILE"
  FINAL_REASON="agent_failed"
  log "Agent execution failed/timed out (exit=$AGENT_EXIT)"
  write_ledger "failed" "$FINAL_REASON"
  linear_comment "**SWARM Execution Incomplete**\n\nAgent failed or timed out for '$ISSUE_IDENTIFIER' (exit=$AGENT_EXIT)."
  linear_transition "Blocked,Backlog,Todo"
  exit 13
fi
log "SWARM execution finished."
heartbeat "agent_invoke" "agent_completed" "running"

if AGENT_SEMANTIC_REASON=$(classify_agent_output "$AGENT_OUTPUT_FILE"); then
  log "Semantic agent-output gate triggered: $AGENT_SEMANTIC_REASON"
fi

# Ensure minimum required docs exist even if agent skipped them.
# Never overwrite user/agent-created files.
ensure_minimum_docs() {
  local repo_name branch now top_dirs spec_path system_design_path api_contracts_path
  repo_name="$(basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)")"
  branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "${ISSUE_IDENTIFIER:-unknown}")"
  now="$(date -u +%FT%TZ)"
  top_dirs="$(find . -maxdepth 2 -type d \
    ! -path '.' \
    ! -path './.git' \
    ! -path './node_modules' \
    ! -path './vendor' \
    ! -path './dist' \
    ! -path './build' \
    | sed 's|^\./||' \
    | sort \
    | head -n 20)"

  spec_path="docs/spec/${ISSUE_IDENTIFIER}.md"
  system_design_path="docs/architecture/SYSTEM_DESIGN.md"
  api_contracts_path="docs/architecture/API_CONTRACTS.md"

  if [ ! -e "$spec_path" ]; then
    mkdir -p "$(dirname "$spec_path")"
    cat > "$spec_path" <<EOF
# ${ISSUE_IDENTIFIER}: ${ISSUE_TITLE:-Untitled Issue}

Generated by adapter fallback on ${now} because the agent did not create this file.

## Summary
${ISSUE_DESCRIPTION:-No issue description provided.}

## Repository Context
- Repository: ${repo_name}
- Branch: ${branch}
- Ticket type: ${TICKET_TYPE}
- Default branch: ${DEFAULT_BRANCH:-unknown}

## Likely Areas Of Impact
$(if [ -n "$top_dirs" ]; then echo "$top_dirs" | sed 's/^/- /'; else echo "- Unable to infer project structure automatically"; fi)

## Minimum Acceptance Criteria
- Required artifacts for this run are present.
- Changes on branch \`${branch}\` align with the issue summary above.
- Validation and review should confirm implementation correctness, tests, and security impact.

## Notes
- This is a fallback spec generated by the adapter.
- Replace with agent-authored planning details when available.
EOF
  fi

  if [ "$TICKET_TYPE" = "architect" ]; then
    if [ ! -e "$system_design_path" ]; then
      mkdir -p "$(dirname "$system_design_path")"
      cat > "$system_design_path" <<EOF
# System Design

Generated by adapter fallback on ${now} because the agent did not create this file.

## Objective
${ISSUE_TITLE:-Architectural update}

## Problem Statement
${ISSUE_DESCRIPTION:-No issue description provided.}

## Proposed Design
- Implement the smallest change that satisfies the issue intent.
- Prefer extending existing modules and interfaces over introducing parallel abstractions.
- Preserve compatibility with the current default branch unless explicitly changed by code in this run.

## Components To Review
$(if [ -n "$top_dirs" ]; then echo "$top_dirs" | sed 's/^/- /'; else echo "- Unable to infer project structure automatically"; fi)

## Risks
- Architectural assumptions may be incomplete because this document was generated without planner output.
- Reviewers should confirm data flow, failure modes, and operational impact.

## Validation
- Confirm changed files match the intended design.
- Confirm tests and security scan cover the affected paths.
EOF
    fi

    if [ ! -e "$api_contracts_path" ]; then
      mkdir -p "$(dirname "$api_contracts_path")"
      cat > "$api_contracts_path" <<EOF
# API Contracts

Generated by adapter fallback on ${now} because the agent did not create this file.

## Scope
This placeholder records the minimum contract expectation for issue \`${ISSUE_IDENTIFIER}\`.

## Contract Changes
- No explicit API contract was documented by the agent.
- Review changed routes, handlers, schemas, DTOs, events, and persistence interfaces in this branch.

## Backward Compatibility Checklist
- Identify any request/response shape changes.
- Identify any new required fields or removed fields.
- Identify any status code, auth, or validation changes.
- Identify any event payload or storage schema changes.

## Reviewer Action
Document concrete contract deltas here before merge if the branch changes externally consumed behavior.
EOF
    fi
  fi
}

heartbeat "artifact_prep" "minimum_docs_ready" "running"
ensure_minimum_docs
heartbeat "artifact_prep" "minimum_docs_complete" "running"

# Ensure security report exists even if agent skipped SAST
ensure_security_scan_report() {
  mkdir -p reports

  if [ -s reports/security_scan.txt ]; then
    return 0
  fi

  {
    echo "Security scan report"
    echo "Generated at: $(date -u +%FT%TZ)"
    echo "Issue: ${ISSUE_IDENTIFIER:-unknown}"
    echo "Branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
    echo

    local ran_any=0

    if command -v semgrep >/dev/null 2>&1; then
      ran_any=1
      echo "=== semgrep ==="
      RUN_HEARTBEAT_PHASE="security_scan" run_with_timeout "semgrep scan" "${SCAN_TIMEOUT_SEC:-180}" semgrep --config auto . 2>&1 || echo "[adapter] semgrep failed or timed out"
      echo
    fi

    if command -v trivy >/dev/null 2>&1; then
      ran_any=1
      echo "=== trivy fs ==="
      RUN_HEARTBEAT_PHASE="security_scan" run_with_timeout "trivy fs scan" "${SCAN_TIMEOUT_SEC:-180}" trivy fs --severity HIGH,CRITICAL --no-progress . 2>&1 || echo "[adapter] trivy failed or timed out"
      echo
    fi

    if command -v npm >/dev/null 2>&1 && [ -f package.json ]; then
      ran_any=1
      echo "=== npm audit ==="
      RUN_HEARTBEAT_PHASE="security_scan" run_with_timeout "npm audit" "${SCAN_TIMEOUT_SEC:-180}" npm audit --audit-level=high 2>&1 || echo "[adapter] npm audit failed or timed out"
      echo
    fi

    if command -v pip-audit >/dev/null 2>&1 && { [ -f requirements.txt ] || [ -f pyproject.toml ]; }; then
      ran_any=1
      echo "=== pip-audit ==="
      RUN_HEARTBEAT_PHASE="security_scan" run_with_timeout "pip-audit" "${SCAN_TIMEOUT_SEC:-180}" pip-audit 2>&1 || echo "[adapter] pip-audit failed or timed out"
      echo
    fi

    if [ "$ran_any" -eq 0 ]; then
      echo "No local SAST/dependency scanner available or supported manifest detected."
      echo "Fallback artifact generated by adapter. Manual review required."
    fi
  } > reports/security_scan.txt
}

heartbeat "security_scan" "security_scan_start" "running"
ensure_security_scan_report
heartbeat "security_scan" "security_scan_complete" "running"

# 4) Git stage/commit/push

# 4) Git stage/commit/push

heartbeat "git_publish" "git_stage_start" "running"
git add -A

if git diff --cached --quiet; then
  log "Nothing staged to commit"
else
  if ! git commit -m "chore: auto-commit SWARM artifacts for $ISSUE_IDENTIFIER" 2>>"$LOG_FILE"; then
    FINAL_REASON="commit_failed"
    log "git commit failed"
    write_ledger "failed" "$FINAL_REASON"
    exit 14
  fi
fi

BASE_SHA="$(git merge-base HEAD "origin/$DEFAULT_BRANCH" 2>/dev/null || true)"
if [ -n "$BASE_SHA" ]; then
  COMMITS_AHEAD="$(git rev-list --count "${BASE_SHA}..HEAD" 2>/dev/null || echo 0)"
  CHANGED_FILES="$(git diff --name-only "${BASE_SHA}..HEAD" 2>/dev/null | wc -l | tr -d ' ')"
else
  COMMITS_AHEAD="$(git rev-list --count "origin/$DEFAULT_BRANCH..HEAD" 2>/dev/null || echo 0)"
  CHANGED_FILES="$(git diff --name-only "origin/$DEFAULT_BRANCH...HEAD" 2>/dev/null | wc -l | tr -d ' ')"
fi

log "Commits ahead of $DEFAULT_BRANCH: $COMMITS_AHEAD"
log "Changed files ahead of $DEFAULT_BRANCH: $CHANGED_FILES"

GIT_TERMINAL_PROMPT=0 RUN_HEARTBEAT_PHASE="git_publish" run_with_timeout "git push" "${GIT_TIMEOUT_SEC:-120}" git push -u --force-with-lease origin HEAD:"$ISSUE_IDENTIFIER" 2>>"$LOG_FILE" || log "Push attempted"
heartbeat "git_publish" "git_push_complete" "running"

# 5) Validate artifacts + quality gate
if [ ! -x "$VALIDATION_SCRIPT" ]; then
  chmod +x "$VALIDATION_SCRIPT" 2>/dev/null || true
fi

heartbeat "validation" "validation_start" "running"
set +e
VALIDATION_RAW=$(VALIDATION_DEFAULT_BRANCH="$DEFAULT_BRANCH" AGENT_SEMANTIC_REASON="$AGENT_SEMANTIC_REASON" RUN_HEARTBEAT_PHASE="validation" run_with_timeout "artifact validation" "${VALIDATION_TIMEOUT_SEC:-30}" bash "$VALIDATION_SCRIPT" "$TICKET_TYPE" "$ISSUE_IDENTIFIER" "$COMMITS_AHEAD")
VAL_EXIT=$?
set -e
if [ $VAL_EXIT -ne 0 ] && [ -z "$VALIDATION_RAW" ]; then
  VALIDATION_JSON='{"valid":false,"reason":"validation_script_failed","missing_artifacts":[],"changed_files":[],"meaningful_changed_files":[],"placeholder_only_files":[],"placeholder_only":false,"status_only_signal":false,"agent_semantic_reason":null,"commits_ahead":0}'
else
  VALIDATION_JSON=$(echo "$VALIDATION_RAW" | jq -c '.' 2>/dev/null || echo '{"valid":false,"reason":"validation_json_parse_error"}')
fi
heartbeat "validation" "validation_complete" "running"
VALID=$(echo "$VALIDATION_JSON" | jq -r '.valid')
REASON=$(echo "$VALIDATION_JSON" | jq -r '.reason')
MISSING_ARR=$(echo "$VALIDATION_JSON" | jq -r '.missing_artifacts | join(", ")')

# Extra sanity gate: require at least 1 changed file for non-test tickets too
if [ "$VALID" = "true" ] && [ "$CHANGED_FILES" -eq 0 ]; then
  VALID="false"
  REASON="no_material_changes"
fi

if [ "$VALID" = "true" ] && [ -n "$AGENT_SEMANTIC_REASON" ]; then
  VALID="false"
  REASON="$AGENT_SEMANTIC_REASON"
  VALIDATION_JSON=$(echo "$VALIDATION_JSON" | jq -c --arg reason "$REASON" '.valid=false | .reason=$reason | .agent_semantic_reason=$reason')
fi

log "Validation Result: $VALIDATION_JSON"

# 6) PR + status updates
if [ "$VALID" = "true" ]; then
  heartbeat "pr_flow" "pr_lookup_start" "running"
  if ! GH_PAGER=cat GH_PROMPT_DISABLED=1 RUN_HEARTBEAT_PHASE="pr_flow" run_with_timeout "gh pr view" "${GH_TIMEOUT_SEC:-60}" gh pr view "$ISSUE_IDENTIFIER" >/dev/null 2>&1; then
    GH_PAGER=cat GH_PROMPT_DISABLED=1 RUN_HEARTBEAT_PHASE="pr_flow" run_with_timeout "gh pr create" "${GH_TIMEOUT_SEC:-120}" gh pr create --title "$ISSUE_TITLE" --body "$ISSUE_DESCRIPTION" 2>> "$LOG_FILE" || log "PR creation attempted"
  fi
  heartbeat "pr_flow" "pr_lookup_complete" "running"
  PR_URL=$(GH_PAGER=cat GH_PROMPT_DISABLED=1 RUN_HEARTBEAT_PHASE="pr_flow" run_with_timeout "gh pr url lookup" "${GH_TIMEOUT_SEC:-60}" gh pr view "$ISSUE_IDENTIFIER" --json url -q .url 2>/dev/null || echo "")
  heartbeat "pr_flow" "pr_url_resolved" "running"
  [ -n "$PR_URL" ] || { VALID="false"; REASON="pr_missing"; }
fi

if [ "$VALID" = "true" ]; then
  FINAL_STATUS="success"
  FINAL_REASON="ok"
  heartbeat "finalize" "success_finalize_start" "$FINAL_STATUS"
  write_ledger "$FINAL_STATUS" "$FINAL_REASON"

  REVIEW_NOTE=""
  if [ "$AUTO_REVIEW_ENABLED" = "true" ] && [ -n "$PR_URL" ]; then
    verdict=$(auto_reviewer_verdict "$PR_URL")
    REVIEW_NOTE="\n\nReviewer verdict: $verdict"
    if [ "$verdict" = "APPROVE" ] && [ "$AUTO_MERGE_ON_APPROVE" = "true" ]; then
      GH_PAGER=cat GH_PROMPT_DISABLED=1 run_with_timeout "gh pr merge" "${GH_TIMEOUT_SEC:-120}" gh pr merge "$PR_URL" --squash --delete-branch 2>>"$LOG_FILE" || true
      linear_transition "Done,Completed,In Review,Review"
    else
      linear_transition "In Review,Review,Done"
    fi
  else
    linear_transition "In Review,Review,Done"
  fi

  COMMENT_BODY="**SWARM Execution Complete!**\n\nPull Request: $PR_URL$REVIEW_NOTE\n\n**Validation Envelope**\n\`\`\`json\n$VALIDATION_JSON\n\`\`\`"
  linear_comment "$COMMENT_BODY"
  log "Adapter finished successfully."
  exit 0
fi

# Failure path
FINAL_STATUS="failed"
FINAL_REASON="$REASON"
heartbeat "finalize" "failure_finalize_start" "$FINAL_STATUS"
write_ledger "$FINAL_STATUS" "$FINAL_REASON"

COMMENT_BODY="**SWARM Execution Incomplete**\n\nNo PR created for '$ISSUE_IDENTIFIER'.\nReason: $REASON"
if [ -n "$MISSING_ARR" ]; then
  COMMENT_BODY="$COMMENT_BODY\n\nMissing required artifacts: $MISSING_ARR"
fi
COMMENT_BODY="$COMMENT_BODY\n\n**Validation Envelope**\n\`\`\`json\n$VALIDATION_JSON\n\`\`\`"
linear_comment "$COMMENT_BODY"
linear_transition "Blocked,Backlog,Todo"

case "$REASON" in
  missing_artifacts) log "Adapter finished with HARD FAILURE: missing artifacts."; exit 2 ;;
  no_commits|no_material_changes|placeholder_only_changes|agent_status_only|agent_launch_only) log "Adapter finished with FAILURE: semantic/material gate rejected run ($REASON)."; exit 3 ;;
  pr_missing) log "Adapter finished with FAILURE: PR missing."; exit 4 ;;
  *) log "Adapter finished with FAILURE: $REASON"; exit 5 ;;
esac
