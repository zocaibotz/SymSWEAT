from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from src.utils.llm import get_llm
from src.utils.logger import logger

llm = get_llm()

def summarize_history(messages: list[BaseMessage]) -> str:
    """
    Summarizes a conversation history into a concise string.
    """
    if not messages:
        return "No history."
        
    prompt = [
        SystemMessage(content="You are a precise summarizer. Compress the following conversation history into a concise summary of key decisions, requirements, and current status. Ignore trivial chit-chat."),
        HumanMessage(content=f"History:\n{messages}")
    ]
    
    try:
        response = llm.invoke(prompt)
        return response.content
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        return "Summary unavailable due to error."

def trim_context(messages: list[BaseMessage], max_messages: int = 20) -> list[BaseMessage]:
    """
    Keeps the context window healthy by summarizing old messages.
    Preserves the most recent `max_messages`.
    """
    if len(messages) <= max_messages:
        return messages
        
    # Split into old and new
    # We keep the first message (usually system prompt if present, though in LangGraph it might be transient)
    # But here we assume strict list.
    
    # Strategy: Summarize everything before the cutoff
    cutoff = len(messages) - max_messages
    to_summarize = messages[:cutoff]
    recent = messages[cutoff:]
    
    logger.info(f"Context Pruning: Summarizing {len(to_summarize)} old messages...")
    summary_text = summarize_history(to_summarize)
    
    # Create a summary message
    summary_message = SystemMessage(content=f"PREVIOUS CONTEXT SUMMARY:\n{summary_text}")
    
    return [summary_message] + recent
