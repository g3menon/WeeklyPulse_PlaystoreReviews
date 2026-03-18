"""
Phase 1 — Structured Logger
==============================
Provides a pre-configured logger for the entire pipeline.

Features:
  - Structured output with timestamps, level, and phase name
  - Console handler with colour-coded levels
  - Reusable across all phases via:
      from phase1_setup.logger import get_logger
      logger = get_logger("phase2_scraper")
"""

import logging
import sys
from datetime import datetime


# ---------------------------------------------------------------------------
# Custom Formatter — clean, readable, structured
# ---------------------------------------------------------------------------
class PulseFormatter(logging.Formatter):
    """
    Format: [TIMESTAMP] [LEVEL] [PHASE] message
    Example: [2026-03-13 23:05:12] [INFO] [phase2_scraper] Scraped 187 reviews
    """

    # ANSI colour codes for terminal output
    COLOURS = {
        logging.DEBUG:    "\033[36m",    # Cyan
        logging.INFO:     "\033[32m",    # Green
        logging.WARNING:  "\033[33m",    # Yellow
        logging.ERROR:    "\033[31m",    # Red
        logging.CRITICAL: "\033[41m",    # Red background
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        colour = self.COLOURS.get(record.levelno, "")
        reset = self.RESET

        level = record.levelname.ljust(8)
        phase = record.name.ljust(20)
        message = record.getMessage()

        return (
            f"{colour}[{timestamp}] [{level}] [{phase}] {message}{reset}"
        )


# ---------------------------------------------------------------------------
# Logger Factory
# ---------------------------------------------------------------------------
def get_logger(phase_name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Create or retrieve a named logger for a specific pipeline phase.

    Args:
        phase_name: Identifier for the phase (e.g. "phase2_scraper")
        level:      Logging level (default: INFO)

    Returns:
        Configured logging.Logger instance

    Usage:
        from phase1_setup.logger import get_logger
        logger = get_logger("phase2_scraper")
        logger.info("Scraped 187 reviews")
    """
    logger = logging.getLogger(phase_name)

    # Avoid adding duplicate handlers if get_logger is called multiple times
    if not logger.handlers:
        logger.setLevel(level)

        # Console handler with our custom formatter
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(PulseFormatter())
        logger.addHandler(console_handler)

    return logger
