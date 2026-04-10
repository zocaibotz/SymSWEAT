#!/bin/bash
# Read prompt from stdin (piped from run_swarm.sh)
USER_PROMPT=$(cat)
SYSTEM_INSTRUCTIONS="
You are executing a task inside the SWARMINSYM orchestration pipeline.
You MUST strictly follow these rules:
1. Do not ask for user confirmation; you are running autonomously.
2. You MUST generate the file \`docs/spec/${ISSUE_IDENTIFIER}.md\`.
3. You MUST generate a security report at \`reports/security_scan.txt\`.
4. If this is an architecture ticket, you MUST generate \`docs/architecture/SYSTEM_DESIGN.md\` and \`docs/architecture/API_CONTRACTS.md\`.
5. You MUST ensure all tests pass.
6. When you are done, output exactly: 'Task completed successfully.'
"
export OPENAI_API_KEY="${MINIMAX_API_KEY}"
export OPENAI_BASE_URL="${MINIMAX_BASE_URL:-https://api.minimax.io/v1}"
aider --model openai/MiniMax-M2.5 --yes-always --no-auto-commits --message "$SYSTEM_INSTRUCTIONS

$USER_PROMPT"
