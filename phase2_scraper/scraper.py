"""
Phase 2 — Review Scraper
=========================
Fetches INDMoney Play Store reviews, filters by date window,
deduplicates, caps at MAX_REVIEWS, and saves to data/reviews_raw.json.

Rules enforced:
  P2.1 — Discard reviews shorter than 30 words
  P2.2 — Cap at MAX_REVIEWS (200)
  P2.3 — Deduplicate by review_id
  P2.4 — Date-window filter (last DATE_WINDOW_WEEKS weeks)
  P2.5 — Only retain safe fields; drop PII-adjacent fields
  P2.6 — Exponential backoff on rate-limit errors (max 3 retries)
"""

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from google_play_scraper import Sort, reviews as gp_reviews
from google_play_scraper.exceptions import NotFoundError
import emoji
from langdetect import detect
from langdetect.lang_detect_exception import LangDetectException

from phase1_setup.config import (
    APP_ID,
    DATE_WINDOW_WEEKS,
    MAX_REVIEWS,
    REVIEWS_RAW_PATH,
)
from phase1_setup.logger import get_logger

logger = get_logger("phase2_scraper")

# ---------------------------------------------------------------------------
# Internal constants
# ---------------------------------------------------------------------------
_FETCH_COUNT = 1000          # How many to request from Play Store
_MAX_RETRIES = 3             # P2.6: exponential backoff retries
_MIN_WORD_COUNT = 30         # P2.1: minimum words in review text
_SAFE_FIELDS = {             # P2.5: only retain non-PII fields
    "review_id", "rating", "text", "date", "thumbs_up"
}


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def scrape_reviews() -> list[dict]:
    """
    Main entry point for Phase 2.
    Scrapes, filters, deduplicates, caps, and saves reviews.

    Returns the list of saved reviews.
    """
    logger.info("Phase 2 — Starting Play Store review scrape")
    logger.info(f"  App ID       : {APP_ID}")
    logger.info(f"  Date window  : last {DATE_WINDOW_WEEKS} weeks")
    logger.info(f"  Cap          : {MAX_REVIEWS} reviews")

    raw_reviews = _fetch_with_retry()
    logger.info(f"  Fetched      : {len(raw_reviews)} raw records from Play Store")

    cutoff_date = _get_cutoff_date()
    logger.info(f"  Cutoff date  : {cutoff_date.date()} (reviews before this are dropped)")

    filtered = _apply_filters(raw_reviews, cutoff_date)
    logger.info(f"  After all filters : {len(filtered)} reviews")

    _save(filtered)
    logger.info(f"Phase 2 — Complete. Saved {len(filtered)} reviews → {REVIEWS_RAW_PATH}")
    return filtered


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_cutoff_date() -> datetime:
    """Returns the oldest allowed review date (UTC-aware)."""
    return datetime.now(timezone.utc) - timedelta(weeks=DATE_WINDOW_WEEKS)


def _fetch_with_retry() -> list[dict]:
    """
    Fetch reviews from the Play Store with exponential backoff.
    P2.6 — max 3 retries on rate-limit / connection errors.
    """
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            result, _ = gp_reviews(
                APP_ID,
                lang="en",
                country="in",
                sort=Sort.NEWEST,
                count=_FETCH_COUNT,
            )
            return result
        except NotFoundError:
            logger.error(f"App '{APP_ID}' not found on Play Store. Check APP_ID.")
            return []
        except Exception as exc:
            wait = 2 ** attempt  # 2, 4, 8 seconds
            if attempt < _MAX_RETRIES:
                logger.warning(
                    f"  Attempt {attempt}/{_MAX_RETRIES} failed ({exc}). "
                    f"Retrying in {wait}s..."
                )
                time.sleep(wait)
            else:
                logger.error(
                    f"  All {_MAX_RETRIES} attempts failed. Last error: {exc}"
                )
                return []
    return []


def _apply_filters(raw: list[dict], cutoff: datetime) -> list[dict]:
    """
    Apply all P2 filtering rules and return a capped list.

    Steps (in order):
      1. Deduplicate by review_id  (P2.3)
      2. Date-window filter        (P2.4)
      3. 30-word minimum           (P2.1)
      4. Keep only safe fields     (P2.5)
      5. Cap at MAX_REVIEWS        (P2.2)
    """
    # P2.3 — Deduplicate by review_id
    seen_ids: set[str] = set()
    unique: list[dict] = []
    for r in raw:
        rid = r.get("reviewId") or r.get("review_id") or ""
        if rid and rid not in seen_ids:
            seen_ids.add(rid)
            unique.append(r)
    logger.info(f"  After dedup          : {len(unique)} (dropped {len(raw) - len(unique)})")

    # P2.4 — Date-window filter
    date_filtered: list[dict] = []
    for r in unique:
        review_date = _parse_date(r)
        if review_date and review_date >= cutoff:
            date_filtered.append(r)
    logger.info(
        f"  After date filter    : {len(date_filtered)} "
        f"(dropped {len(unique) - len(date_filtered)})"
    )

    # P2.10 & P2.7 — Remove Emojis and English-only filter
    english_filtered: list[dict] = []
    for r in date_filtered:
        raw_text = (r.get("content") or r.get("text") or "")
        clean_text = emoji.replace_emoji(raw_text, replace="") # Strip emojis
        r["content"] = clean_text # Update dictionary inplace
        if clean_text.strip():
            try:
                lang = detect(clean_text)
                if lang == "en":
                    english_filtered.append(r)
            except LangDetectException:
                pass # Un-detectable languages are dropped

    logger.info(
        f"  After English filter : {len(english_filtered)} "
        f"(dropped {len(date_filtered) - len(english_filtered)})"
    )

    # P2.1 — 30-word minimum
    word_filtered: list[dict] = []
    for r in english_filtered:
        text = (r.get("content") or r.get("text") or "").strip()
        if len(text.split()) >= _MIN_WORD_COUNT:
            word_filtered.append(r)
    logger.info(
        f"  After word filter    : {len(word_filtered)} "
        f"(dropped {len(english_filtered) - len(word_filtered)} <{_MIN_WORD_COUNT} words)"
    )

    # P2.5 & P2.9 — Map to safe schema, drop PII-adjacent fields and title
    safe: list[dict] = [_to_safe_schema(r) for r in word_filtered]

    # P2.8 — Sort by thumbs_up descending
    safe.sort(key=lambda x: x["thumbs_up"], reverse=True)

    # P2.2 — Cap at MAX_REVIEWS
    capped = safe[:MAX_REVIEWS]
    if len(safe) > MAX_REVIEWS:
        logger.info(f"  Capped at {MAX_REVIEWS} (had {len(safe)} after filters)")

    return capped


def _parse_date(review: dict) -> datetime | None:
    """
    Parse the review date from the Play Store response dict.
    Returns a UTC-aware datetime, or None if unparseable.
    """
    at = review.get("at")
    if isinstance(at, datetime):
        # google-play-scraper returns naive datetime; treat as UTC
        if at.tzinfo is None:
            return at.replace(tzinfo=timezone.utc)
        return at
    if isinstance(at, str):
        try:
            from dateutil import parser as dparser
            dt = dparser.parse(at)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return None
    return None


def _to_safe_schema(r: dict) -> dict:
    """
    Convert a raw Play Store review dict to our clean schema.
    Only safe, non-PII fields are included (P2.5).
    """
    # Play Store fields: reviewId, score, title, content, at, thumbsUpCount
    review_date_obj = _parse_date(r)
    date_str = review_date_obj.strftime("%Y-%m-%d") if review_date_obj else ""

    return {
        "review_id": r.get("reviewId") or r.get("review_id") or "",
        "rating": int(r.get("score") or r.get("rating") or 0),
        "text": (r.get("content") or r.get("text") or "").strip(),
        "date": date_str,
        "thumbs_up": int(r.get("thumbsUpCount") or r.get("thumbs_up") or 0),
    }


def _save(reviews: list[dict]) -> None:
    """Save the review list to REVIEWS_RAW_PATH as pretty-printed JSON."""
    REVIEWS_RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REVIEWS_RAW_PATH, "w", encoding="utf-8") as f:
        json.dump(reviews, f, ensure_ascii=False, indent=2)
    logger.info(f"  Saved → {REVIEWS_RAW_PATH} ({REVIEWS_RAW_PATH.stat().st_size} bytes)")


# ---------------------------------------------------------------------------
# Standalone execution
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    scrape_reviews()
