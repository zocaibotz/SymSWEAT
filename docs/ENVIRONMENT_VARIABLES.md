# SWEAT Environment Variables

This document defines runtime configuration for SWEAT.

## Provider/API credentials

| Key | Purpose | SWEAT-specific? |
|---|---|---|
| `OPENAI_API_KEY` | OpenAI provider access | No |
| `ANTHROPIC_API_KEY` | Anthropic provider access | No |
| `GEMINI_API_KEY` | Gemini provider access | No |
| `MOONSHOT_API_KEY` | Moonshot/Kimi provider access | No |
| `MINIMAX_API_KEY` | Minimax provider access | No |
| `TAVILY_API_KEY` | Tavily web research/search | No |

## External integrations

| Key | Purpose | SWEAT-specific? |
|---|---|---|
| `LINEAR_API_KEY` | Linear API auth | No |
| `LINEAR_TEAM_ID` | Linear team/workspace target | **Partially** (depends on your SWEAT Linear setup) |
| `N8N_WEBHOOK_URL` | n8n callback/webhook target | **Partially** (depends on SWEAT workflow topology) |
| `N8N_API_KEY` | n8n API auth | No |

## SWEAT routing/toggles

| Key | Purpose | SWEAT-specific? |
|---|---|---|
| `SWEAT_USE_CODEX_CLI` | Enable Codex CLI coder path | **Yes** |
| `SWEAT_USE_OLLAMA` | Enable local Ollama usage | **Yes** |
| `SWEAT_USE_MINIMAX` | Enable Minimax usage path | **Yes** |
| `SWEAT_CODER_PRIMARY` | Primary coder model route | **Yes** |
| `SWEAT_CODER_SECONDARY` | Secondary coder model route | **Yes** |
| `SWEAT_CODER_TERTIARY` | Tertiary coder model route | **Yes** |
| `SWEAT_LLM_PRIMARY` | Primary non-coder LLM route | **Yes** |
| `SWEAT_LLM_SECONDARY` | Secondary non-coder LLM route | **Yes** |
| `SWEAT_LLM_TERTIARY` | Tertiary non-coder LLM route | **Yes** |

## Model selection/compatibility

| Key | Purpose | SWEAT-specific? |
|---|---|---|
| `MODEL_NAME` | Global/default model hint used by SWEAT scripts | **Yes** |
| `GEMINI_CLI_MODEL` | Gemini CLI model selection | **Partially** |
| `MINIMAX_BASE_URL` | Minimax endpoint override | No |
| `MINIMAX_MODEL` | Minimax model id override | No |

## Which variables are "very SWEAT project specific"?

Most SWEAT-specific keys are the `SWEAT_*` namespace and routing controls:

- `SWEAT_USE_CODEX_CLI`
- `SWEAT_USE_OLLAMA`
- `SWEAT_USE_MINIMAX`
- `SWEAT_CODER_PRIMARY`
- `SWEAT_CODER_SECONDARY`
- `SWEAT_CODER_TERTIARY`
- `SWEAT_LLM_PRIMARY`
- `SWEAT_LLM_SECONDARY`
- `SWEAT_LLM_TERTIARY`
- `MODEL_NAME`

These encode SWEAT’s orchestration strategy rather than provider credentials.
