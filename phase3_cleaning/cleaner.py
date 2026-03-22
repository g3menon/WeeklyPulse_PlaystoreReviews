"""
Phase 3 — Data Cleaning & PII Removal
=====================================
Loads raw reviews from data/reviews_raw.json, applies PII removal,
filters out gibberish/profanity, normalizes text, and saves to
data/reviews_cleaned.json.

Rules enforced:
  P3.1 — Strip all PII using regex patterns (Emails, Phones, Aadhaar-style IDs)
  P3.2 — Remove gibberish and nonsensical text
  P3.3 — Filter out hate speech, slang, and abusive language
  P3.4 — Re-apply the 30-word minimum after cleaning
  P3.5 — Normalise whitespace and fix encoding
  P3.6 — Log cleaning statistics
"""

import json
import re
from phase1_setup.config import REVIEWS_RAW_PATH, REVIEWS_CLEANED_PATH
from phase1_setup.logger import get_logger

logger = get_logger("phase3_cleaning")

# Regex patterns for PII
EMAIL_REGEX = re.compile(r'[\w.-]+@[\w.-]+\.\w+')
PHONE_REGEX = re.compile(r'\+?\d[\d\s-]{7,}\d')
AADHAAR_REGEX = re.compile(r'\d{4}\s?\d{4}\s?\d{4}')

# Profanity list (lightweight keyword-based filter)
BAD_WORDS = {
    "fuck", "shit", "bitch", "asshole", "cunt", "dick", "bastard", 
    "slut", "whore", "motherfucker", "fucker"
}

def clean_reviews() -> list[dict]:
    """
    Main entry point for Phase 3.
    Loads raw reviews, cleans them, and saves the result.
    """
    logger.info("Phase 3 — Starting data cleaning and PII removal")
    
    if not REVIEWS_RAW_PATH.exists():
        logger.error(f"Raw reviews file not found at {REVIEWS_RAW_PATH}. Please run Phase 2 first.")
        return []

    with open(REVIEWS_RAW_PATH, "r", encoding="utf-8") as f:
        raw_reviews = json.load(f)

    logger.info(f"  Loaded       : {len(raw_reviews)} raw reviews")

    stats = {
        "total_input": len(raw_reviews),
        "pii_stripped": 0,
        "gibberish_dropped": 0,
        "profanity_dropped": 0,
        "short_dropped": 0,
        "final_output": 0
    }

    cleaned_reviews = []

    for review in raw_reviews:
        text = review.get("text", "")

        # P3.5 - Normalise whitespace and fix encoding
        # Fix common UTF-8 artefacts like â€™ -> '
        text = text.replace("â€™", "'").replace("â€œ", '"').replace("â€", '"')
        
        # P3.1 - Strip PII (Order matters: Aadhaar before Phone to avoid greediness)
        original_text = text
        text = EMAIL_REGEX.sub("[EMAIL]", text)
        text = AADHAAR_REGEX.sub("[ID]", text)
        text = PHONE_REGEX.sub("[PHONE]", text)
        
        if text != original_text:
            stats["pii_stripped"] += 1

        # Drop rule checks
        if _is_profane(text):
            stats["profanity_dropped"] += 1
            continue
            
        if _is_gibberish(text):
            stats["gibberish_dropped"] += 1
            continue

        # Normalise whitespace (collapse multiple spaces, strip leading/trailing)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # P3.4 - Re-apply the 30-word minimum
        words = text.split()
        if len(words) < 30:
            stats["short_dropped"] += 1
            continue

        review["text"] = text
        cleaned_reviews.append(review)

    stats["final_output"] = len(cleaned_reviews)

    # P3.6 - Log cleaning statistics
    logger.info("  Cleaning Stats:")
    logger.info(f"    Total input      : {stats['total_input']}")
    logger.info(f"    PII reviews      : {stats['pii_stripped']}")
    logger.info(f"    Profanity dropped: {stats['profanity_dropped']}")
    logger.info(f"    Gibberish dropped: {stats['gibberish_dropped']}")
    logger.info(f"    Short dropped    : {stats['short_dropped']}")
    logger.info(f"    Final output     : {stats['final_output']}")

    _save(cleaned_reviews)
    logger.info(f"Phase 3 — Complete. Saved {len(cleaned_reviews)} reviews → {REVIEWS_CLEANED_PATH}")

    return cleaned_reviews

def _is_profane(text: str) -> bool:
    """Check for hate speech, slang, and abusive language (P3.3)."""
    words = set(re.findall(r'\b\w+\b', text.lower()))
    return bool(words.intersection(BAD_WORDS))

def _is_gibberish(text: str) -> bool:
    """
    Remove gibberish and nonsensical text (P3.2).
    If a review has > 50% non-dictionary words or consists of repeated characters.
    """
    # Check for repeated characters (e.g., "aaaaa")
    if re.search(r'(.)\1{4,}', text):
        return True

    words = text.split()
    if not words:
        return True

    non_dict_count = 0
    for word in words:
        word_lower = word.lower()
        # Simple heuristic for non-dictionary a.k.a unpronounceable:
        # Check if it has no vowels but is longer than 3 characters (e.g. "hjkl")
        if len(word_lower) > 3 and not any(v in word_lower for v in 'aeiouy'):
            non_dict_count += 1
            continue
            
        # Check if we have consecutive consonants > 4
        if re.search(r'[bcdfghjklmnpqrstvwxz]{5,}', word_lower):
             non_dict_count += 1
             continue

    if (non_dict_count / len(words)) > 0.5:
        return True

    return False

def _save(reviews: list[dict]) -> None:
    """Save cleaned reviews."""
    REVIEWS_CLEANED_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REVIEWS_CLEANED_PATH, "w", encoding="utf-8") as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    clean_reviews()
