"""
Phase 1 — Test Suite
======================
Tests for config, logger, and LLM clients.

Run:
    python -m pytest tests/test_phase1.py -v
    # or
    python tests/test_phase1.py
"""

import os
import sys
import logging
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_logger():
    """Test 1: Logger creates structured output without errors."""
    print("\n" + "=" * 60)
    print("TEST 1: Logger")
    print("=" * 60)

    from phase1_setup.logger import get_logger

    logger = get_logger("test_phase1")

    # Should not raise
    logger.info("Logger initialised successfully")
    logger.debug("This is a debug message (may not show at INFO level)")
    logger.warning("This is a warning message")

    # Verify logger has a handler
    assert len(logger.handlers) > 0, "Logger should have at least one handler"

    # Verify name is correct
    assert logger.name == "test_phase1", f"Expected 'test_phase1', got '{logger.name}'"

    # Calling get_logger again should NOT add duplicate handlers
    logger2 = get_logger("test_phase1")
    assert len(logger2.handlers) == 1, (
        f"Duplicate handlers detected: {len(logger2.handlers)}"
    )

    print("[PASS] Logger test PASSED\n")


def test_config_constants():
    """Test 2: Pipeline constants are defined correctly."""
    print("=" * 60)
    print("TEST 2: Config Constants")
    print("=" * 60)

    # These imports don't need env vars — they're plain constants
    from phase1_setup.config import (
        APP_ID,
        PLAY_STORE_URL,
        DATE_WINDOW_WEEKS,
        MAX_REVIEWS,
        MAX_THEMES,
        MIN_THEMES,
        GROQ_MODEL,
        GEMINI_MODEL,
        DATA_DIR,
        PROJECT_ROOT as CONFIG_ROOT,
    )

    assert APP_ID == "in.indwealth", f"APP_ID should be 'in.indwealth', got '{APP_ID}'"
    assert "in.indwealth" in PLAY_STORE_URL, "Play Store URL should contain app ID"
    assert DATE_WINDOW_WEEKS == 8, f"Expected 8 weeks, got {DATE_WINDOW_WEEKS}"
    assert MAX_REVIEWS == 200, f"Expected 200 max reviews, got {MAX_REVIEWS}"
    assert MIN_THEMES == 3, f"Expected 3 min themes, got {MIN_THEMES}"
    assert MAX_THEMES == 5, f"Expected 5 max themes, got {MAX_THEMES}"
    assert GROQ_MODEL == "llama-3.3-70b-versatile", f"Unexpected Groq model: {GROQ_MODEL}"
    assert "gemini-2.5-flash" in GEMINI_MODEL, f"Unexpected Gemini model: {GEMINI_MODEL}"
    assert DATA_DIR.exists(), f"Data directory should exist: {DATA_DIR}"

    print(f"  APP_ID           = {APP_ID}")
    print(f"  DATE_WINDOW      = {DATE_WINDOW_WEEKS} weeks")
    print(f"  MAX_REVIEWS      = {MAX_REVIEWS}")
    print(f"  GROQ_MODEL       = {GROQ_MODEL}")
    print(f"  GEMINI_MODEL     = {GEMINI_MODEL}")
    print(f"  DATA_DIR         = {DATA_DIR}")
    print("[PASS] Config constants test PASSED\n")


def test_config_settings():
    """Test 3: Settings object loads env vars and has safe repr."""
    print("=" * 60)
    print("TEST 3: Settings Object")
    print("=" * 60)

    from phase1_setup.config import settings

    # Settings should have all required attributes
    assert hasattr(settings, "groq_api_key"), "Missing groq_api_key"
    assert hasattr(settings, "gemini_api_key"), "Missing gemini_api_key"
    assert hasattr(settings, "email_address"), "Missing email_address"
    assert hasattr(settings, "email_app_password"), "Missing email_app_password"
    assert hasattr(settings, "port"), "Missing port"

    # Keys should not be empty
    assert len(settings.groq_api_key) > 0, "groq_api_key is empty"
    assert len(settings.gemini_api_key) > 0, "gemini_api_key is empty"
    assert len(settings.email_address) > 0, "email_address is empty"

    # Safe repr should NOT leak full keys
    repr_str = repr(settings)
    assert settings.groq_api_key not in repr_str, "SECURITY: Full Groq key leaked in repr!"
    assert settings.gemini_api_key not in repr_str, "SECURITY: Full Gemini key leaked in repr!"
    assert "****" in repr_str, "repr should mask the email password"

    print(f"  Settings loaded: {settings}")
    print("[PASS] Settings test PASSED\n")


def test_groq_client():
    """Test 4: Groq client initialises and can make a simple call."""
    print("=" * 60)
    print("TEST 4: Groq Client")
    print("=" * 60)

    from phase1_setup.llm_clients import groq_client

    # Test a simple chat call
    response = groq_client.chat(
        prompt="Reply with exactly: GROQ_OK",
        system_prompt="You are a test bot. Reply with exactly what the user asks.",
        temperature=0.0,
        max_tokens=10,
    )

    assert response is not None, "Groq response should not be None"
    assert len(response.strip()) > 0, "Groq response should not be empty"

    print(f"  Groq response: {response.strip()}")
    print("[PASS] Groq client test PASSED\n")


def test_gemini_client():
    """Test 5: Gemini client initialises and can generate text."""
    print("=" * 60)
    print("TEST 5: Gemini 2.5 Flash Client")
    print("=" * 60)

    from phase1_setup.llm_clients import gemini_client

    # Test a simple generation call
    response = gemini_client.generate(
        prompt="Reply with exactly: GEMINI_OK"
    )

    assert response is not None, "Gemini response should not be None"
    assert len(response.strip()) > 0, "Gemini response should not be empty"

    print(f"  Gemini response: {response.strip()}")
    print("[PASS] Gemini 2.5 Flash client test PASSED\n")


def test_data_directory():
    """Test 6: Data directory exists and is writable."""
    print("=" * 60)
    print("TEST 6: Data Directory")
    print("=" * 60)

    from phase1_setup.config import DATA_DIR

    assert DATA_DIR.exists(), f"Data dir should exist: {DATA_DIR}"
    assert DATA_DIR.is_dir(), f"Data dir should be a directory: {DATA_DIR}"

    # Test writability
    test_file = DATA_DIR / "_test_write.tmp"
    try:
        test_file.write_text("test")
        assert test_file.exists(), "Test file should have been created"
        print(f"  Data directory: {DATA_DIR}")
        print(f"  Writable: YES")
    finally:
        test_file.unlink(missing_ok=True)

    print("[PASS] Data directory test PASSED\n")


# ---------------------------------------------------------------------------
# Run all tests
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  Phase 1 -- Setup & Configuration Tests")
    print("=" * 60)

    passed = 0
    failed = 0
    total = 6
    tests = [
        ("Logger", test_logger),
        ("Config Constants", test_config_constants),
        ("Settings Object", test_config_settings),
        ("Groq Client", test_groq_client),
        ("Gemini Client", test_gemini_client),
        ("Data Directory", test_data_directory),
    ]

    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            failed += 1
            print(f"[FAIL] {name} test FAILED: {e}\n")

    print("=" * 60)
    print(f"  Results: {passed}/{total} passed, {failed}/{total} failed")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)
    else:
        print("  All Phase 1 tests passed!")
        sys.exit(0)
