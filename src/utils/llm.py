import os
import shutil
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from dotenv import load_dotenv

from src.utils.cli_llm import GeminiCLIModel, CodexCLIModel, OpenCodeCLIModel

load_dotenv()


def _is_likely_real_key(value: str | None) -> bool:
    if not value:
        return False
    v = value.strip()
    if not v:
        return False
    placeholders = ["fake", "your_", "changeme", "replace_me", "dummy", "test"]
    return not any(p in v.lower() for p in placeholders)


def _gemini_api_model() -> BaseChatModel:
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)


def _minimax_api_model() -> BaseChatModel:
    """Best-effort MiniMax via OpenAI-compatible chat endpoint."""
    base_url = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.io/v1")
    model = os.getenv("MINIMAX_MODEL", "MiniMax-M2.5")
    return ChatOpenAI(api_key=os.getenv("MINIMAX_API_KEY"), base_url=base_url, model=model, temperature=0)


def _codex_cli_model() -> BaseChatModel:
    return CodexCLIModel(model_name=os.getenv("SWEAT_CODEX_CLI_MODEL", "codex-custom"))


def _gemini_cli_model() -> BaseChatModel:
    return GeminiCLIModel(model_name=os.getenv("SWEAT_GEMINI_CLI_MODEL", "gemini-2.5-flash"))


def _opencode_cli_model() -> BaseChatModel:
    return OpenCodeCLIModel(model_name=os.getenv("SWEAT_OPENCODE_CLI_MODEL", "opencode"))


def _ollama_model() -> BaseChatModel:
    from langchain_ollama import ChatOllama
    model = os.getenv("SWEAT_OLLAMA_MODEL", "llama3.2:1b")
    return ChatOllama(model=model, temperature=0)


from langchain_community.chat_models import FakeListChatModel

def _create_fallback_chain(primary_model: BaseChatModel, fallback_models: list[BaseChatModel]) -> BaseChatModel:
    """Wraps a model with a list of fallbacks."""
    if not fallback_models:
        return primary_model
    # langchain-core's with_fallbacks returns a RunnableBinding, which acts like a model
    return primary_model.with_fallbacks(fallback_models)

def _main_alias_factories(model_name: str = "gemini-2.5-flash"):
    return {
        "codex_cli": lambda: _codex_cli_model(),
        "opencode_cli": lambda: _opencode_cli_model() if shutil.which("opencode") else None,
        "gemini_cli": lambda: GeminiCLIModel(model_name=os.getenv("SWEAT_GEMINI_CLI_MODEL", model_name)),
        "gemini_api": lambda: _gemini_api_model() if _is_likely_real_key(os.getenv("GEMINI_API_KEY")) else None,
        "minimax_api": lambda: _minimax_api_model() if _is_likely_real_key(os.getenv("MINIMAX_API_KEY")) else None,
        "ollama": lambda: _ollama_model(),
        "openai": lambda: ChatOpenAI(model="gpt-4o", temperature=0) if _is_likely_real_key(os.getenv("OPENAI_API_KEY")) else None,
        "anthropic": lambda: ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0) if _is_likely_real_key(os.getenv("ANTHROPIC_API_KEY")) else None,
    }


def _resolve_main_alias_order():
    # Keep all agents on same model policy as coder by default.
    primary = os.getenv("SWEAT_LLM_PRIMARY", os.getenv("SWEAT_CODER_PRIMARY", "codex_cli"))
    secondary = os.getenv("SWEAT_LLM_SECONDARY", os.getenv("SWEAT_CODER_SECONDARY", "gemini_cli"))
    tertiary = os.getenv("SWEAT_LLM_TERTIARY", os.getenv("SWEAT_CODER_TERTIARY", "ollama"))
    order = [primary, secondary, tertiary]
    for alias in ["openai", "anthropic", "gemini_api", "minimax_api", "ollama", "gemini_cli", "opencode_cli", "codex_cli"]:
        if alias not in order:
            order.append(alias)
    seen = set()
    return [a for a in order if not (a in seen or seen.add(a))]


def get_llm(model_name: str = "gemini-2.5-flash") -> BaseChatModel:
    """Main reasoning LLM using explicit primary->secondary->tertiary model policy."""

    # Hard overrides remain supported.
    if os.getenv("SWEAT_USE_MINIMAX", "false").lower() in {"1", "true", "yes", "on"}:
        try:
            print("[MainLLM] Forced primary: minimax_api")
            return _minimax_api_model()
        except Exception as e:
            print(f"[MainLLM] MiniMax override failed: {e}")

    if os.getenv("SWEAT_USE_OLLAMA", "false").lower() in {"1", "true", "yes", "on"}:
        try:
            model = os.getenv("SWEAT_OLLAMA_MODEL", "llama3.2:1b")
            print(f"[MainLLM] Forced primary: ollama ({model})")
            return _ollama_model()
        except Exception as e:
            print(f"[MainLLM] Ollama override failed: {e}")

    factories = _main_alias_factories(model_name=model_name)
    order = _resolve_main_alias_order()

    built = []
    for alias in order:
        fn = factories.get(alias)
        if not fn:
            continue
        try:
            model = fn()
            if model is not None:
                built.append((alias, model))
        except Exception as e:
            print(f"[MainLLM] model init failed for {alias}: {e}")

    if built:
        names = [n for n, _ in built]
        print(f"[MainLLM] effective model order: {' -> '.join(names)}")
        primary = built[0][1]
        fallbacks = [m for _, m in built[1:]]
        return _create_fallback_chain(primary, fallbacks)

    print("[MainLLM] no configured models available; using safe mock fallback")
    return FakeListChatModel(responses=["[MOCK MAIN FALLBACK] No model backend available."])


def get_coder_llm() -> BaseChatModel:
    """
    Coder LLM with automatic fallback.
    """
    
    # Priority 0: Forced MiniMax
    if os.getenv("SWEAT_USE_MINIMAX", "false").lower() in {"1", "true", "yes", "on"}:
        try:
            print("Using MiniMax as Coder LLM (env override).")
            return _minimax_api_model()
        except Exception as e:
            print(f"MiniMax init failed: {e}")

    # Priority 1: Forced Ollama
    if os.getenv("SWEAT_USE_OLLAMA", "false").lower() in {"1", "true", "yes", "on"}:
        try:
            from langchain_ollama import ChatOllama
            model = os.getenv("SWEAT_OLLAMA_MODEL", "llama3.2:1b")
            print(f"Using Ollama ({model}) as Coder LLM (env override).")
            return ChatOllama(model=model, temperature=0)
        except Exception as e:
            print(f"Ollama import failed: {e}")

    if _is_likely_real_key(os.getenv("OPENAI_API_KEY")):
        return ChatOpenAI(model="gpt-4o", temperature=0)

    if _is_likely_real_key(os.getenv("ANTHROPIC_API_KEY")):
        return ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0)

    # Fallback stack
    fallbacks = []

    # 0. MiniMax API fallback
    if _is_likely_real_key(os.getenv("MINIMAX_API_KEY")):
        try:
            fallbacks.append(_minimax_api_model())
        except Exception as e:
            print(f"MiniMax init failed: {e}")
    
    # 1. Gemini CLI
    if shutil.which("gemini"):
        fallbacks.append(GeminiCLIModel(model_name="gemini-2.5-flash"))
        
    # 2. Mock
    fallbacks.append(FakeListChatModel(responses=["def fallback_code():\n    print('Quota limit hit, using mock code')"]))

    # Optional: Codex CLI Override
    use_codex = os.getenv("SWEAT_USE_CODEX_CLI", "false").lower() in {"1", "true", "yes", "on"}
    if use_codex and shutil.which("codex"):
        print("Using Codex CLI as Coder LLM (env override).")
        return _create_fallback_chain(CodexCLIModel(model_name="codex-custom"), fallbacks)

    # Primary: Gemini API
    if _is_likely_real_key(os.getenv("GEMINI_API_KEY")):
        try:
            print("Using Gemini API (langchain-google-genai) as Coder LLM.")
            primary = _gemini_api_model()
            return _create_fallback_chain(primary, fallbacks)
        except Exception as e:
            print(f"Gemini API init failed: {e}")

    # Fallback to CLI as primary
    if shutil.which("gemini"):
        print("Using Gemini CLI as Coder LLM fallback.")
        return _create_fallback_chain(GeminiCLIModel(model_name="gemini-2.5-flash"), [fallbacks[-1]])

    return fallbacks[-1]

# --- SWEAT coder routing override (explicit ordered fallback) ---

def _coder_alias_factories():
    return {
        "codex_cli": lambda: _codex_cli_model(),
        "opencode_cli": lambda: _opencode_cli_model() if shutil.which("opencode") else None,
        "gemini_cli": lambda: _gemini_cli_model(),
        "gemini_api": lambda: _gemini_api_model() if _is_likely_real_key(os.getenv("GEMINI_API_KEY")) else None,
        "minimax_api": lambda: _minimax_api_model() if _is_likely_real_key(os.getenv("MINIMAX_API_KEY")) else None,
        "ollama": lambda: _ollama_model(),
        "openai": lambda: ChatOpenAI(model="gpt-4o", temperature=0) if _is_likely_real_key(os.getenv("OPENAI_API_KEY")) else None,
        "anthropic": lambda: ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0) if _is_likely_real_key(os.getenv("ANTHROPIC_API_KEY")) else None,
    }


def _resolve_coder_alias_order():
    primary = os.getenv("SWEAT_CODER_PRIMARY", "gemini_cli")
    secondary = os.getenv("SWEAT_CODER_SECONDARY", "codex_cli")
    tertiary = os.getenv("SWEAT_CODER_TERTIARY", "minimax_api")
    order = [primary, secondary, tertiary]

    # Extend with sensible defaults if not already present.
    for alias in ["openai", "anthropic", "gemini_api", "opencode_cli", "ollama"]:
        if alias not in order:
            order.append(alias)
    # de-dup preserve order
    seen = set()
    order = [a for a in order if not (a in seen or seen.add(a))]
    return order


def get_coder_llm() -> BaseChatModel:
    """
    Returns coder model chain with explicit ordered fallback.

    Default order (configurable):
      SWEAT_CODER_PRIMARY   (default codex_cli)
      SWEAT_CODER_SECONDARY (default gemini_cli)
      SWEAT_CODER_TERTIARY  (default minimax_api)
    """
    # Hard overrides remain supported.
    if os.getenv("SWEAT_USE_MINIMAX", "false").lower() in {"1", "true", "yes", "on"}:
        try:
            print("[CodeSmith] Forced primary: minimax_api")
            return _minimax_api_model()
        except Exception as e:
            print(f"[CodeSmith] MiniMax override failed: {e}")

    if os.getenv("SWEAT_USE_OLLAMA", "false").lower() in {"1", "true", "yes", "on"}:
        try:
            model = os.getenv("SWEAT_OLLAMA_MODEL", "llama3.2:1b")
            print(f"[CodeSmith] Forced primary: ollama ({model})")
            return _ollama_model()
        except Exception as e:
            print(f"[CodeSmith] Ollama override failed: {e}")

    if os.getenv("SWEAT_USE_CODEX_CLI", "false").lower() in {"1", "true", "yes", "on"}:
        # Keep explicit codex override as top of the ordered chain.
        os.environ.setdefault("SWEAT_CODER_PRIMARY", "codex_cli")

    factories = _coder_alias_factories()
    order = _resolve_coder_alias_order()

    built = []
    for alias in order:
        fn = factories.get(alias)
        if not fn:
            continue
        try:
            model = fn()
            if model is not None:
                built.append((alias, model))
        except Exception as e:
            print(f"[CodeSmith] model init failed for {alias}: {e}")

    if built:
        names = [n for n, _ in built]
        print(f"[CodeSmith] effective model order: {' -> '.join(names)}")
        primary = built[0][1]
        fallbacks = [m for _, m in built[1:]]
        return _create_fallback_chain(primary, fallbacks)

    print("[CodeSmith] no configured models available; using fake fallback")
    return FakeListChatModel(responses=[
        '{"tool":"write_file","args":{"path":"src/app.py","content":"print(\\"Hello from fake coder fallback!\\")"}}'
    ])
