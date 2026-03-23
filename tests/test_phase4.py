import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from phase4_themes.theme_generator import ThemeGenerator

@pytest.fixture
def mock_reviews():
    return [
        {"review_id": "r1", "text": "The app crashes a lot on my phone."},
        {"review_id": "r2", "text": "I love the new UI, but pricing is high."},
        {"review_id": "r3", "text": "Customer support was very helpful."}
    ]

@pytest.fixture
def theme_generator():
    return ThemeGenerator()

def test_discover_themes_success(theme_generator, mock_reviews):
    with patch.object(theme_generator.client, "chat") as mock_chat:
        mock_chat.return_value = '[\"Performance\", \"UI/UX\", \"Customer Support\", \"Pricing\", \"Positive Feedback\"]'
        
        themes = theme_generator.discover_themes(mock_reviews)
        
        assert len(themes) == 5
        assert "Performance" in themes
        assert mock_chat.call_count == 1

def test_discover_themes_retry_on_invalid_count(theme_generator, mock_reviews):
    with patch.object(theme_generator.client, "chat") as mock_chat:
        # First returns 2 themes (invalid, needs 5-7), then returns 5 themes
        mock_chat.side_effect = [
            '[\"Performance\", \"UI/UX\"]',
            '[\"Performance\", \"UI/UX\", \"Customer Support\", \"Pricing\", \"Positive Feedback\"]'
        ]
        
        themes = theme_generator.discover_themes(mock_reviews)
        
        assert len(themes) == 5
        assert mock_chat.call_count == 2

def test_discover_themes_fallback(theme_generator, mock_reviews):
    with patch.object(theme_generator.client, "chat") as mock_chat:
        # Fails both times
        mock_chat.side_effect = [
            '[\"Performance\", \"UI\"]',
            '[\"Performance\", \"UI\"]'
        ]
        
        themes = theme_generator.discover_themes(mock_reviews)
        
        assert len(themes) == 2 # Rule says if fails, use the raw response/fallback

def test_classify_reviews_success(theme_generator, mock_reviews):
    themes = ["Performance", "UI/UX", "Pricing", "Positive Feedback", "Support"]
    with patch.object(theme_generator.client, "chat") as mock_chat:
        mock_chat.return_value = '{"r1": ["Performance"], "r2": ["Pricing", "UI/UX"], "r3": ["Support", "Positive Feedback"]}'
        
        results = theme_generator.classify_reviews(mock_reviews, themes)
        
        assert len(results) == 3
        assert results[0]["themes"] == ["Performance"]
        assert "Pricing" in results[1]["themes"]
        assert "UI/UX" in results[1]["themes"]

def test_run_phase4_end_to_end(theme_generator, mock_reviews, tmp_path):
    input_path = tmp_path / "cleaned.json"
    output_path = tmp_path / "classified.json"
    
    with open(input_path, "w", encoding="utf-8") as f:
        json.dump(mock_reviews, f)
        
    with patch.object(theme_generator.client, "chat") as mock_chat:
        # First call is for themes, second is for classification
        mock_chat.side_effect = [
            '[\"Performance\", \"UI/UX\", \"Pricing\", \"Customer Support\", \"Positive Feedback\"]',
            '{"r1": ["Performance"], "r2": ["UI/UX", "Pricing"], "r3": ["Positive Feedback"]}'
        ]
        
        results = theme_generator.run(str(input_path), str(output_path))
        
        assert len(results) == 3
        assert results[0]["themes"] == ["Performance"]
        
        # Verify output saved
        assert output_path.exists()
        with open(output_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
            assert len(saved_data) == 3
            assert saved_data[0]["themes"] == ["Performance"]
