import subprocess
import json
import os
from typing import List, Optional, Any, Dict
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.outputs import ChatResult, ChatGeneration

class GeminiCLIModel(BaseChatModel):
    """
    Wrapper for the Google Gemini CLI.
    Usage: gemini -p "PROMPT" --output-format json
    """
    model_name: str = "gemini-1.5-pro"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        prompt = self._messages_to_prompt(messages)
        
        # Command to run Gemini CLI
        # We use -p for prompt, --output-format text for raw output
        # Note: escaping quotes in shell commands is tricky. 
        # We'll use subprocess with list args to handle escaping.
        command = ["gemini", "-p", prompt, "--output-format", "text"]
        
        try:
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                check=True,
                timeout=45
            )
            output = result.stdout.strip()
        except subprocess.TimeoutExpired:
            output = "Error calling Gemini CLI: timed out after 45s"
        except subprocess.CalledProcessError as e:
            output = f"Error calling Gemini CLI: {e.stderr}"
            
        message = AIMessage(content=output)
        return ChatResult(generations=[ChatGeneration(message=message)])

    def _messages_to_prompt(self, messages: List[BaseMessage]) -> str:
        """Converts LangChain messages to a single string prompt."""
        prompt_parts = []
        for m in messages:
            if isinstance(m, SystemMessage):
                prompt_parts.append(f"System: {m.content}")
            elif isinstance(m, HumanMessage):
                prompt_parts.append(f"User: {m.content}")
            elif isinstance(m, AIMessage):
                prompt_parts.append(f"Assistant: {m.content}")
            else:
                prompt_parts.append(f"{m.type}: {m.content}")
        return "\n".join(prompt_parts)

    @property
    def _llm_type(self) -> str:
        return "gemini-cli"

class CodexCLIModel(BaseChatModel):
    """
    Wrapper for GitHub Copilot CLI (gh copilot).
    """
    model_name: str = "codex-cli"

    # Path to manually installed binary
    # We found `gh copilot` doesn't pick it up automatically in this environment.
    # So we call the binary directly.
    binary_path: str = os.path.expanduser("~/.local/share/gh/copilot/gh-copilot")

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        prompt = self._messages_to_prompt(messages)

        # Manually call the binary we downloaded
        command = [self.binary_path, "suggest", "-t", "shell", prompt]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=45
            )
            if result.returncode != 0:
                output = f"Error calling Copilot: {result.stderr.strip() or 'Unknown error'}"
            else:
                output = result.stdout.strip()
                # Copilot CLI often outputs an explanation then a command.
                # We want the content.
        except subprocess.TimeoutExpired:
            output = "Error calling Copilot/Codex CLI: timed out after 45s"
        except Exception as e:
            output = f"System Error calling Copilot: {str(e)}"

        message = AIMessage(content=output)
        return ChatResult(generations=[ChatGeneration(message=message)])

    def _messages_to_prompt(self, messages: List[BaseMessage]) -> str:
        return "\n".join([m.content for m in messages])

    @property
    def _llm_type(self) -> str:
        return "codex-cli"


class OpenCodeCLIModel(BaseChatModel):
    """
    Wrapper for OpenCode CLI.
    Uses: opencode run "<prompt>"
    """
    model_name: str = "opencode"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        prompt = self._messages_to_prompt(messages)
        command = ["opencode", "run", prompt]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode != 0:
                output = f"Error calling OpenCode CLI: {result.stderr.strip() or 'Unknown error'}"
            else:
                output = result.stdout.strip() or ""
        except subprocess.TimeoutExpired:
            output = "Error calling OpenCode CLI: timed out after 60s"
        except Exception as e:
            output = f"System Error calling OpenCode CLI: {str(e)}"

        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=output))])

    def _messages_to_prompt(self, messages: List[BaseMessage]) -> str:
        return "\n".join([m.content for m in messages])

    @property
    def _llm_type(self) -> str:
        return "opencode-cli"
