"""
Phase 2 — Test Suite
======================
Tests for the Play Store scraper (phase2_scraper/scraper.py).

Run:
    python -m pytest tests/test_phase2.py -v
    # or
    python tests/test_phase2.py

Tests:
  1. _parse_date handles datetime objects and strings correctly
  2. _to_safe_schema maps Play Store fields to our schema
  3. _apply_filters enforces dedup, date-window, word-count, and cap
  4. Output file schema validation
  5. Live scrape integration test (writes real data/reviews_raw.json)
"""

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Helpers shared across tests
# ---------------------------------------------------------------------------
def _make_raw_review(
    rid: str = "gp:abc123",
    score: int = 4,
    title: str = "Good app",
    content: str = "This is a great application with many useful features for investment.",
    days_ago: int = 5,
    thumbs: int = 3,
) -> dict:
    """Create a synthetic raw Play Store review dict."""
    return {
        "reviewId": rid,
        "score": score,
        "title": title,
        "content": content,
        "at": datetime.now(timezone.utc) - timedelta(days=days_ago),
        "thumbsUpCount": thumbs,
    }


# ---------------------------------------------------------------------------
# Test 1 — _parse_date
# ---------------------------------------------------------------------------
def test_parse_date_datetime_object():
    """Test 1: _parse_date correctly handles datetime objects."""
    print("\n" + "=" * 60)
    print("TEST 1: _parse_date — datetime objects")
    print("=" * 60)

    from phase2_scraper.scraper import _parse_date

    naive_dt = datetime(2026, 3, 15, 10, 0, 0)
    result = _parse_date({"at": naive_dt})
    assert result is not None, "Should return a datetime"
    assert result.tzinfo is not None, "Should be timezone-aware"
    assert result.year == 2026

    aware_dt = datetime(2026, 3, 15, 10, 0, 0, tzinfo=timezone.utc)
    result2 = _parse_date({"at": aware_dt})
    assert result2 == aware_dt, "Should return aware datetime unchanged"

    result_none = _parse_date({})
    assert result_none is None, "Missing key should return None"

    print("[PASS] _parse_date datetime test PASSED\n")


# ---------------------------------------------------------------------------
# Test 2 — _to_safe_schema
# ---------------------------------------------------------------------------
def test_to_safe_schema():
    """Test 2: _to_safe_schema maps Play Store fields correctly (P2.5)."""
    print("=" * 60)
    print("TEST 2: _to_safe_schema — field mapping and PII exclusion")
    print("=" * 60)

    from phase2_scraper.scraper import _to_safe_schema

    raw = _make_raw_review(
        rid="gp:XYZ789",
        score=3,
        title="  Needs Improvement  ",
        content="The app is okay but has some issues with navigation and loading speed lately.",
        days_ago=10,
        thumbs=5,
    )
    # Add some PII-ish fields to simulate what Play Store might return
    raw["userImage"] = "https://example.com/avatar.jpg"
    raw["userName"] = "SomeUser"

    result = _to_safe_schema(raw)

    # Check correct fields are present
    assert set(result.keys()) == {"review_id", "rating", "text", "date", "thumbs_up"}, \
        f"Schema mismatch: {result.keys()}"

    assert result["review_id"] == "gp:XYZ789"
    assert result["rating"] == 3
    assert "loading speed" in result["text"]
    assert result["thumbs_up"] == 5

    # No PII fields
    assert "userImage" not in result
    assert "userName" not in result

    # Date is YYYY-MM-DD format
    datetime.strptime(result["date"], "%Y-%m-%d")  # raises if wrong format

    print(f"  Schema: {list(result.keys())}")
    print("[PASS] _to_safe_schema test PASSED\n")


# ---------------------------------------------------------------------------
# Test 3 — _apply_filters: deduplication (P2.3)
# ---------------------------------------------------------------------------
def test_apply_filters_deduplication():
    """Test 3a: _apply_filters removes duplicate review_ids (P2.3)."""
    print("=" * 60)
    print("TEST 3a: _apply_filters — deduplication")
    print("=" * 60)

    from phase2_scraper.scraper import _apply_filters, _get_cutoff_date

    cutoff = _get_cutoff_date()
    # Create 3 reviews but 2 share the same reviewId
    dup_content = (
        "This application is very feature rich and I use it daily for stock market "
        "trading and investing my hard earned money into various mutual funds and stocks. "
        "The overall experience has been extremely positive and I highly recommend it to everyone."
    )
    reviews = [
        _make_raw_review(rid="gp:001", content=dup_content),
        _make_raw_review(rid="gp:001", content=dup_content),  # duplicate
        _make_raw_review(rid="gp:002", content="Fantastic app for portfolio management though it could have better UI design and color themes for the overall user experience. I think the developers should improve the performance on older devices."),
    ]
    result = _apply_filters(reviews, cutoff)
    ids = [r["review_id"] for r in result]
    assert ids.count("gp:001") == 1, "Duplicate should be removed"
    assert "gp:002" in ids
    print("[PASS] Deduplication test PASSED\n")


# ---------------------------------------------------------------------------
# Test 3b — _apply_filters: date-window filter (P2.4)
# ---------------------------------------------------------------------------
def test_apply_filters_date_window():
    """Test 3b: _apply_filters drops reviews older than DATE_WINDOW_WEEKS (P2.4)."""
    print("=" * 60)
    print("TEST 3b: _apply_filters — date-window")
    print("=" * 60)

    from phase2_scraper.scraper import _apply_filters, _get_cutoff_date

    cutoff = _get_cutoff_date()
    long_text = (
        "This is a very detailed and comprehensive review about the investment "
        "application and its many features for stock market tracking, mutual fund "
        "management, and portfolio analysis. The app performs well overall but "
        "has some areas that could use improvement in terms of user experience."
    )

    recent = _make_raw_review(rid="gp:recent", content=long_text, days_ago=10)
    old = _make_raw_review(rid="gp:old", content=long_text, days_ago=70)  # > 8 weeks

    result = _apply_filters([recent, old], cutoff)
    ids = [r["review_id"] for r in result]
    assert "gp:recent" in ids, "Recent review should pass"
    assert "gp:old" not in ids, "Old review should be dropped"
    print("[PASS] Date-window filter test PASSED\n")


# ---------------------------------------------------------------------------
# Test 3c — _apply_filters: 30-word minimum (P2.1)
# ---------------------------------------------------------------------------
def test_apply_filters_word_count():
    """Test 3c: _apply_filters drops reviews with < 30 words (P2.1)."""
    print("=" * 60)
    print("TEST 3c: _apply_filters — 30-word minimum")
    print("=" * 60)

    from phase2_scraper.scraper import _apply_filters, _get_cutoff_date

    cutoff = _get_cutoff_date()
    short = _make_raw_review(rid="gp:short", content="Good app")  # < 30 words
    long_text = (
        "This is a very detailed review about the INDMoney application. "
        "It has many features for investment and portfolio management. "
        "I use it every day for tracking my stocks and mutual funds."
    )
    long_rev = _make_raw_review(rid="gp:long", content=long_text)

    result = _apply_filters([short, long_rev], cutoff)
    ids = [r["review_id"] for r in result]
    assert "gp:short" not in ids, "Short review should be filtered"
    assert "gp:long" in ids, "Long review should pass"
    print("[PASS] Word-count filter test PASSED\n")


# ---------------------------------------------------------------------------
# Test 3d — _apply_filters: cap at MAX_REVIEWS (P2.2)
# ---------------------------------------------------------------------------
def test_apply_filters_cap():
    """Test 3d: _apply_filters caps output at MAX_REVIEWS (P2.2)."""
    print("=" * 60)
    print("TEST 3d: _apply_filters — cap at MAX_REVIEWS")
    print("=" * 60)

    from phase2_scraper.scraper import _apply_filters, _get_cutoff_date, _MIN_WORD_COUNT
    from phase1_setup.config import MAX_REVIEWS

    cutoff = _get_cutoff_date()
    # Create MAX_REVIEWS + 10 unique, recent, long-enough reviews
    long_text = (
        "This is an absolutely fantastic and wonderful application designed carefully "
        "for stock market investment and portfolio management. I really love using it "
        "every single day for tracking my personal finances and staying up to date."
    )
    many = [
        _make_raw_review(rid=f"gp:{i:04d}", content=long_text, days_ago=1, thumbs=i)
        for i in range(MAX_REVIEWS + 10)
    ]

    result = _apply_filters(many, cutoff)
    assert len(result) <= MAX_REVIEWS, f"Should be capped at {MAX_REVIEWS}, got {len(result)}"
    # Check if sorting worked (should have the highest thumbs_up)
    assert result[0]["thumbs_up"] == MAX_REVIEWS + 9
    assert result[-1]["thumbs_up"] == 10
    print(f"  Produced {len(result)} reviews (cap: {MAX_REVIEWS})")
    print("[PASS] Cap test PASSED\n")


# ---------------------------------------------------------------------------
# Test 4 — Output schema validation
# ---------------------------------------------------------------------------
def test_output_schema():
    """Test 4: scrape_reviews() produces correct schema with mocked data."""
    print("=" * 60)
    print("TEST 4: Output schema validation (mocked scrape)")
    print("=" * 60)

    from phase2_scraper.scraper import scrape_reviews, _MIN_WORD_COUNT
    from phase1_setup.config import REVIEWS_RAW_PATH

    long_text = (
        "This is a very comprehensive review about the INDMoney application. "
        "I use it daily for investment tracking and mutual fund management. "
        "The interface is clean but could use some improvements in the navigation."
    )

    mock_reviews = [
        {
            "reviewId": f"gp:mock{i:04d}",
            "score": (i % 5) + 1,
            "title": f"Review {i}",
            "content": long_text,
            "at": datetime.now(timezone.utc) - timedelta(days=i % 30 + 1),
            "thumbsUpCount": i * 2,
        }
        for i in range(10)
    ]

    with patch("phase2_scraper.scraper.gp_reviews", return_value=(mock_reviews, None)):
        reviews = scrape_reviews()

    assert isinstance(reviews, list), "Should return a list"
    assert len(reviews) > 0, "Should return at least one review"

    required_keys = {"review_id", "rating", "text", "date", "thumbs_up"}
    for rev in reviews:
        missing = required_keys - rev.keys()
        assert not missing, f"Review missing keys: {missing}"
        assert isinstance(rev["rating"], int), "Rating must be int"
        assert 1 <= rev["rating"] <= 5, f"Rating out of range: {rev['rating']}"
        datetime.strptime(rev["date"], "%Y-%m-%d")  # validates format

    # Verify file was written
    assert REVIEWS_RAW_PATH.exists(), "reviews_raw.json should exist"
    with open(REVIEWS_RAW_PATH, encoding="utf-8") as f:
        loaded = json.load(f)
    assert isinstance(loaded, list), "File should contain a JSON array"
    assert len(loaded) == len(reviews)

    print(f"  Validated {len(reviews)} reviews")
    print(f"  File: {REVIEWS_RAW_PATH}")
    print("[PASS] Schema validation test PASSED\n")


# ---------------------------------------------------------------------------
# Test 5 — Live integration test (real scrape)
# ---------------------------------------------------------------------------
def test_live_scrape():
    """
    Test 5: Live integration test — actually hits the Play Store.
    Verifies real reviews are returned and schema is correct.
    """
    print("=" * 60)
    print("TEST 5: Live scrape integration (real Play Store)")
    print("=" * 60)

    from phase2_scraper.scraper import scrape_reviews
    from phase1_setup.config import REVIEWS_RAW_PATH

    reviews = scrape_reviews()

    assert isinstance(reviews, list), "Should return a list"
    assert len(reviews) > 0, "Should return at least some reviews"

    required_keys = {"review_id", "rating", "text", "date", "thumbs_up"}
    for rev in reviews[:5]:  # spot-check first 5
        missing = required_keys - rev.keys()
        assert not missing, f"Review missing keys: {missing}"
        assert len(rev["text"].split()) >= 30, "All reviews should have >= 30 words"

    # Verify no PII-adjacent fields
    pii_fields = {"userName", "userImage", "replyContent", "repliedAt"}
    for rev in reviews:
        unexpected = pii_fields & rev.keys()
        assert not unexpected, f"PII field found: {unexpected}"

    assert REVIEWS_RAW_PATH.exists(), "Output file should exist"
    print(f"  Scraped {len(reviews)} live reviews")
    print(f"  First review: {reviews[0]['date']} — {reviews[0]['text'][:80]}...")
    print("[PASS] Live scrape test PASSED\n")


# ---------------------------------------------------------------------------
# Test 6 & 7 — Emoji and language
# ---------------------------------------------------------------------------
def test_apply_filters_emoji_language():
    """Test 6 & 7: _apply_filters drops english and emojis."""
    print("=" * 60)
    print("TEST 6 & 7: _apply_filters — emoji & language")
    print("=" * 60)

    from phase2_scraper.scraper import _apply_filters, _get_cutoff_date
    cutoff = _get_cutoff_date()

    long_text = (
        "This is a very detailed review about the INDMoney application. 🚀 "
        "It has many features for investment and portfolio management. 👍 "
        "I use it every day for tracking my stocks and mutual funds! 😊😊😀"
    )
    foreign_text = (
        "Este es un comentario muy detallado sobre la aplicación INDMoney. "
        "Tiene muchas funciones para la inversión y la gestión de carteras. "
        "Lo uso todos los días para realizar un seguimiento de mis acciones y fondos mutuos."
    )
    rev_emoji = _make_raw_review(rid="gp:emoji", content=long_text)
    rev_foreign = _make_raw_review(rid="gp:foreign", content=foreign_text)

    result = _apply_filters([rev_emoji, rev_foreign], cutoff)
    ids = [r["review_id"] for r in result]
    assert "gp:foreign" not in ids, "Foreign should be dropped"
    assert "gp:emoji" in ids, "Emoji review should pass"
    assert "🚀" not in result[0]["text"], "Emojis should be stripped"
    assert "👍" not in result[0]["text"], "Emojis should be stripped"

    print("[PASS] Emoji and language filter test PASSED\n")

# ---------------------------------------------------------------------------
# Run all tests
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  Phase 2 — Review Scraper Tests")
    print("=" * 60)

    passed = 0
    failed = 0
    tests = [
        ("_parse_date", test_parse_date_datetime_object),
        ("_to_safe_schema", test_to_safe_schema),
        ("Deduplication (P2.3)", test_apply_filters_deduplication),
        ("Date-window (P2.4)", test_apply_filters_date_window),
        ("Word-count (P2.1)", test_apply_filters_word_count),
        ("Cap (P2.2)", test_apply_filters_cap),
        ("Language and Emoji", test_apply_filters_emoji_language),
        ("Schema validation", test_output_schema),
        ("Live scrape", test_live_scrape),
    ]

    for name, fn in tests:
        try:
            fn()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"[FAIL] {name} — {e}\n")

    total = len(tests)
    print("=" * 60)
    print(f"  Results: {passed}/{total} passed, {failed}/{total} failed")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)
    else:
        print("  All Phase 2 tests passed! ✅")
        sys.exit(0)
