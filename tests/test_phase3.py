import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import phase3_cleaning.cleaner as cleaner

@pytest.fixture
def mock_raw_data():
    # Provide test data with enough words to pass 30-word minimum where needed
    base_text_valid = "This is a great app with lots of nice features. " + " ".join(["apple"] * 20) + " "
    return [
        {
            "review_id": "r1",
            "rating": 5,
            "text": base_text_valid + "My email is test@example.com and phone is +91-9876543210. Also ID 1234 5678 9012.",
            "date": "2023-10-01",
            "thumbs_up": 10
        },
        {
            "review_id": "r2",
            "rating": 1,
            "text": "This app is a piece of shit. " + " ".join(["bad"] * 25),
            "date": "2023-10-02",
            "thumbs_up": 5
        },
        {
            "review_id": "r3",
            "rating": 2,
            "text": "aaaaaaa bbb ccc. " + " ".join(["zzzzzzz"] * 25),
            "date": "2023-10-03",
            "thumbs_up": 0
        },
        {
            "review_id": "r4",
            "rating": 4,
            "text": base_text_valid + "I really love the app â€™ and the new UI.",
            "date": "2023-10-04",
            "thumbs_up": 2
        },
        {
            "review_id": "r5", 
            "rating": 3,
            "text": "Too short.",
            "date": "2023-10-05",
            "thumbs_up": 1
        }
    ]

def test_clean_reviews(mock_raw_data, tmp_path):
    raw_path = tmp_path / "raw.json"
    cleaned_path = tmp_path / "cleaned.json"
    
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(mock_raw_data, f)
        
    with patch("phase3_cleaning.cleaner.REVIEWS_RAW_PATH", raw_path), \
         patch("phase3_cleaning.cleaner.REVIEWS_CLEANED_PATH", cleaned_path):
         
        results = cleaner.clean_reviews()
        
        assert len(results) == 2
        
        # r1 is valid but requires PII stripping
        assert "[EMAIL]" in results[0]["text"]
        assert "[PHONE]" in results[0]["text"]
        assert "[ID]" in results[0]["text"]
        
        # r4 is valid and requires encoding fix
        assert "â€™" not in results[1]["text"]
        assert "'" in results[1]["text"]

def test_missing_raw_file(tmp_path):
    raw_path = tmp_path / "does_not_exist.json"
    with patch("phase3_cleaning.cleaner.REVIEWS_RAW_PATH", raw_path):
        results = cleaner.clean_reviews()
        assert results == []
