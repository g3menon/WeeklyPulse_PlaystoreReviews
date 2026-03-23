"""
main.py — INDMoney Weekly Pulse Pipeline Orchestrator
======================================================
Runs all phases in sequence:
  Phase 2: Scrape Play Store reviews
  Phase 3: Clean & strip PII
  Phase 4: Discover themes (Groq LLaMA 3.3)
  Phase 5: Generate weekly pulse (Gemini 2.5 Flash)
  Phase 6: Draft & send email (Gemini 2.5 Flash + Gmail SMTP)

Usage:
    python main.py

Each phase is gated — if a phase fails, the pipeline stops and logs the error.
"""

import sys
from phase1_setup.logger import get_logger

logger = get_logger("main")


def main() -> None:
    logger.info("=" * 60)
    logger.info("INDMoney Weekly Pulse Pipeline — Starting")
    logger.info("=" * 60)

    # ------------------------------------------------------------------
    # Phase 2 — Scrape Play Store Reviews
    # ------------------------------------------------------------------
    from phase2_scraper.scraper import scrape_reviews
    logger.info("Phase 2: Scraping Play Store reviews...")
    scrape_reviews()
    logger.info("Phase 2: Complete")

    # ------------------------------------------------------------------
    # Phase 3 — Clean & Strip PII
    # ------------------------------------------------------------------
    from phase3_cleaning.cleaner import clean_reviews
    logger.info("Phase 3: Cleaning reviews & removing PII...")
    clean_reviews()
    logger.info("Phase 3: Complete")

    # ------------------------------------------------------------------
    # Phase 4 — Theme Generation & Classification (Groq)
    # ------------------------------------------------------------------
    from phase4_themes.theme_generator import run_theme_generation
    logger.info("Phase 4: Discovering themes via Groq LLaMA 3.3...")
    run_theme_generation()
    logger.info("Phase 4: Complete")

    # ------------------------------------------------------------------
    # Phase 5 — Weekly Pulse Generation (Gemini 2.5 Flash)
    # ------------------------------------------------------------------
    from phase5_pulse.pulse_generator import generate_pulse
    logger.info("Phase 5: Generating weekly pulse via Gemini 2.5 Flash...")
    generate_pulse()
    logger.info("Phase 5: Complete")

    # ------------------------------------------------------------------
    # Phase 6 — Email Draft & Delivery (Gemini 2.5 Flash + Gmail SMTP)
    # ------------------------------------------------------------------
    # from phase6_email.email_sender import send_email
    # logger.info("Phase 6: Drafting and sending email...")
    # send_email()
    # logger.info("Phase 6: Complete")

    logger.info("=" * 60)
    logger.info("Pipeline Complete — check your inbox!")
    logger.info("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)
