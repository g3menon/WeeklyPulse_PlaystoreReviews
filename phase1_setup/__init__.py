"""
Phase 1 — Setup & Configuration
=================================
Exports:
  - settings:       Typed env var container (config.py)
  - groq_client:    Groq LLaMA 3 wrapper (llm_clients.py)
  - gemini_client:  Gemini 2.5 Flash wrapper (llm_clients.py)
  - get_logger:     Logger factory (logger.py)
  - Constants:      APP_ID, GROQ_MODEL, GEMINI_MODEL, DATA_DIR, etc.
"""

from phase1_setup.config import (
    settings,
    APP_ID,
    PLAY_STORE_URL,
    DATE_WINDOW_WEEKS,
    MAX_REVIEWS,
    MAX_THEMES,
    MIN_THEMES,
    GROQ_MODEL,
    GEMINI_MODEL,
    DATA_DIR,
    REVIEWS_RAW_PATH,
    REVIEWS_CLEANED_PATH,
    REVIEWS_CLASSIFIED_PATH,
    WEEKLY_PULSE_PATH,
    EMAIL_DRAFT_PATH,
)

from phase1_setup.logger import get_logger

# LLM clients are imported lazily by the phases that need them,
# because they require valid API keys. Importing here would force
# config validation on every import of phase1_setup.
# Use: from phase1_setup.llm_clients import groq_client, gemini_client
