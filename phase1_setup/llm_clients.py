"""
Phase 1 — LLM Client Wrappers
================================
Thin wrappers around the Groq and Google Gemini clients.

Design goals:
  - Initialise once, reuse everywhere
  - Centralised error handling for API failures
  - Easy to mock in tests

Usage:
    from phase1_setup.llm_clients import groq_client, gemini_client
"""

from groq import Groq
from google import genai

from phase1_setup.config import settings, GROQ_MODEL, GEMINI_MODEL
from phase1_setup.logger import get_logger

logger = get_logger("llm_clients")


# ---------------------------------------------------------------------------
# Groq Client  (used by Phase 4 — Theme Generation & Classification)
# ---------------------------------------------------------------------------
class GroqClient:
    """
    Wrapper around the Groq SDK for LLaMA 3 inference.

    Provides a simple `chat()` method that handles:
      - Model selection (defaults to GROQ_MODEL constant)
      - Temperature control
      - Error logging
    """

    def __init__(self, api_key: str):
        self._client = Groq(api_key=api_key)
        logger.info(f"Groq client initialised (model: {GROQ_MODEL})")

    def chat(
        self,
        prompt: str,
        system_prompt: str = "You are a helpful product analyst.",
        temperature: float = 0.3,
        max_tokens: int = 4096,
        model: str = GROQ_MODEL,
    ) -> str:
        """
        Send a chat completion request to Groq.

        Args:
            prompt:        User message content
            system_prompt: System instruction (sets the LLM's role)
            temperature:   Creativity control (0.0–1.0)
            max_tokens:    Maximum response length
            model:         Model identifier (default: llama-3.3-70b-versatile)

        Returns:
            The assistant's response text

        Raises:
            Exception: Logged and re-raised on API failure
        """
        try:
            response = self._client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            raise

    @property
    def raw_client(self) -> Groq:
        """Access the underlying Groq SDK client if needed."""
        return self._client


# ---------------------------------------------------------------------------
# Gemini Client  (used by Phase 5 & 6 — Pulse Generation & Email)
# ---------------------------------------------------------------------------
class GeminiClient:
    """
    Wrapper around the Google GenAI SDK for Gemini 2.5 Flash.

    Provides a simple `generate()` method that handles:
      - Model selection (defaults to GEMINI_MODEL constant)
      - Error logging
    """

    def __init__(self, api_key: str):
        self._client = genai.Client(api_key=api_key)
        logger.info(f"Gemini client initialised (model: {GEMINI_MODEL})")

    def generate(
        self,
        prompt: str,
        model: str = GEMINI_MODEL,
    ) -> str:
        """
        Send a content generation request to Gemini 2.5 Flash.

        Args:
            prompt: The full prompt text
            model:  Model identifier (default: gemini-2.5-flash-preview-04-17)

        Returns:
            The model's response text

        Raises:
            Exception: Logged and re-raised on API failure
        """
        try:
            response = self._client.models.generate_content(
                model=model,
                contents=prompt,
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise

    @property
    def raw_client(self) -> genai.Client:
        """Access the underlying GenAI client if needed."""
        return self._client


# ---------------------------------------------------------------------------
# Singleton Instances — import these directly
# ---------------------------------------------------------------------------
groq_client = GroqClient(api_key=settings.groq_api_key)
gemini_client = GeminiClient(api_key=settings.gemini_api_key)
