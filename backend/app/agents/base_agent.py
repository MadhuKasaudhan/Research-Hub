"""Base agent class for Groq LLM interactions."""

import logging
import time
from dataclasses import dataclass
from groq import Groq

from app.config import get_settings

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "llama-3.3-70b-versatile"


@dataclass
class AgentResponse:
    """Standard response from an agent."""

    content: str
    sources: list[str]
    tokens_used: int


def get_groq_client() -> Groq:
    """Get Groq client instance."""
    settings = get_settings()
    api_key = settings.groq_api_key
    if not api_key:
        logger.warning("[AGENT] GROQ_API_KEY not set. LLM calls will fail.")
    return Groq(api_key=api_key)


class BaseAgent:
    """Base class for all AI agents using Groq API."""

    def __init__(self, model: str = DEFAULT_MODEL) -> None:
        self.model = model
        self.client = get_groq_client()

    def run(
        self,
        prompt: str,
        system_prompt: str,
        context: str | None = None,
        conversation_history: list[dict[str, str]] | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.3,
    ) -> AgentResponse:
        """Execute a Groq API call with retry logic.

        Args:
            prompt: The user's message/question
            system_prompt: System instructions for the agent
            context: Optional context (retrieved chunks, etc.)
            conversation_history: Previous messages in the conversation
            max_tokens: Maximum response tokens
            temperature: Sampling temperature

        Returns:
            AgentResponse with content and token usage
        """
        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

        # Add context if provided
        if context:
            messages.append(
                {
                    "role": "system",
                    "content": f"Relevant context from research papers:\n\n{context}",
                }
            )

        # Add conversation history
        if conversation_history:
            messages.extend(conversation_history)

        # Add current user prompt
        messages.append({"role": "user", "content": prompt})

        # Retry logic: 3 attempts with exponential backoff
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                logger.info(
                    "[AGENT] Groq API call attempt %d for model %s",
                    attempt + 1,
                    self.model,
                )
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )

                content = response.choices[0].message.content or ""
                tokens_used = response.usage.total_tokens if response.usage else 0

                logger.info(
                    "[AGENT] Groq API response received. Tokens used: %d", tokens_used
                )

                return AgentResponse(
                    content=content,
                    sources=[],
                    tokens_used=tokens_used,
                )

            except Exception as e:
                last_error = e
                wait_time = 2**attempt
                logger.warning(
                    "[AGENT] Groq API attempt %d failed: %s. Retrying in %ds...",
                    attempt + 1,
                    str(e),
                    wait_time,
                )
                time.sleep(wait_time)

        # All retries failed
        error_msg = (
            f"Failed to get response from Groq API after 3 attempts: {str(last_error)}"
        )
        logger.error("[AGENT] %s", error_msg)
        return AgentResponse(
            content="I apologize, but I'm unable to process your request at the moment. Please try again later.",
            sources=[],
            tokens_used=0,
        )
