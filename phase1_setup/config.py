"""
Phase 1 — Configuration Module
================================
Centralised configuration loader for the INDMoney Weekly Pulse pipeline.

Loads environment variables from a .env file and exposes them as a
typed settings object. All other phases import from here — this is
the single source of truth for every configurable value.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load .env file from the project root (one level up from phase1_setup/)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# ---------------------------------------------------------------------------
# Pipeline Constants
# ---------------------------------------------------------------------------
APP_ID = "in.indwealth"                          # INDMoney Play Store ID
PLAY_STORE_URL = (
    "https://play.google.com/store/apps/details"
    "?id=in.indwealth&hl=en_IN"
)
DATE_WINDOW_WEEKS = 8                             # How far back to scrape
MAX_REVIEWS = 200                                 # Cap for LLM token control
MAX_THEMES = 5                                    # Upper bound on themes
MIN_THEMES = 3                                    # Lower bound on themes

# LLM Model identifiers
GROQ_MODEL = "llama-3.3-70b-versatile"
GEMINI_MODEL = "gemini-2.5-flash"

# Data directory for pipeline outputs
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# Data file paths
REVIEWS_RAW_PATH = DATA_DIR / "reviews_raw.json"
REVIEWS_CLEANED_PATH = DATA_DIR / "reviews_cleaned.json"
REVIEWS_CLASSIFIED_PATH = DATA_DIR / "reviews_classified.json"
WEEKLY_PULSE_PATH = DATA_DIR / "weekly_pulse.json"
FEE_EXPLANATION_PATH = DATA_DIR / "fee_explanation.json"
EMAIL_DRAFT_PATH = DATA_DIR / "email_draft.html"

# Phase 10A Config
FEE_FUND_URL = "https://www.indmoney.com/mutual-funds/hdfc-pharma-and-healthcare-fund-direct-growth-1044289"


# ---------------------------------------------------------------------------
# Environment Variable Loader
# ---------------------------------------------------------------------------
class Settings:
    """
    Typed container for all environment-driven settings.
    Validates that required variables are present on instantiation.
    """

    def __init__(self):
        # --- Required API keys ---
        self.groq_api_key: str = self._require("GROQ_API_KEY")
        self.gemini_api_key: str = self._require("GEMINI_API_KEY")

        # --- Required email credentials ---
        self.email_address: str = self._require("EMAIL_ADDRESS")
        self.email_app_password: str = self._require("EMAIL_APP_PASSWORD")

        # --- Optional ---
        self.port: int = int(os.getenv("PORT", "8501"))

    # ----- helpers --------------------------------------------------------

    @staticmethod
    def _require(var_name: str) -> str:
        """Fetch an env var or exit with a clear error message."""
        value = os.getenv(var_name)
        if not value:
            print(
                f"\n❌  Missing required environment variable: {var_name}\n"
                f"    → Copy .env.example to .env and fill in your values.\n"
                f"    → Path checked: {ENV_PATH}\n"
            )
            sys.exit(1)
        return value

    def __repr__(self) -> str:
        """Safe repr that never leaks secrets."""
        return (
            f"Settings(\n"
            f"  groq_api_key   = {'*' * 8}...{self.groq_api_key[-4:]},\n"
            f"  gemini_api_key = {'*' * 8}...{self.gemini_api_key[-4:]},\n"
            f"  email_address  = {self.email_address},\n"
            f"  email_password = ****,\n"
            f"  port           = {self.port}\n"
            f")"
        )


# ---------------------------------------------------------------------------
# Singleton — imported by all phases as `from phase1_setup.config import settings`
# ---------------------------------------------------------------------------
settings = Settings()
