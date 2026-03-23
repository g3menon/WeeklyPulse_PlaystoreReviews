import json
import pytest
from unittest.mock import patch, MagicMock
from phase5_pulse.pulse_generator import PulseGenerator

@pytest.fixture
def mock_reviews():
    return [
        {"review_id": "r1", "text": "App crashes a lot.", "rating": 2, "date": "2026-03-01", "themes": ["App Performance"]},
        {"review_id": "r2", "text": "Good app but slow.", "rating": 3, "date": "2026-03-02", "themes": ["App Performance"]},
        {"review_id": "r3", "text": "Support is bad.", "rating": 1, "date": "2026-03-03", "themes": ["Customer Support"]},
        {"review_id": "r4", "text": "I like the new theme.", "rating": 5, "date": "2026-03-04", "themes": ["UI/UX"]},
        {"review_id": "r5", "text": "Another positive review.", "rating": 5, "date": "2026-03-05", "themes": ["UI/UX", "App Performance"]},
        {"review_id": "r6", "text": "Pricing is too high.", "rating": 2, "date": "2026-03-05", "themes": ["Pricing"]}
    ]

@pytest.fixture
def pulse_generator():
    return PulseGenerator()

def test_generate_pulse_success(pulse_generator, mock_reviews):
    mock_json_response = '''
    {
      "top_themes": [
        {"rank": 1, "name": "App Performance", "review_count": 3, "avg_rating": 3.3, "explanation": "Users complain about crashes."},
        {"rank": 2, "name": "UI/UX", "review_count": 2, "avg_rating": 5.0, "explanation": "Users love the new design."},
        {"rank": 3, "name": "Customer Support", "review_count": 1, "avg_rating": 1.0, "explanation": "Users feel support is lacking."}
      ],
      "user_quotes": [
        {"quote": "App crashes a lot.", "theme": "App Performance", "rating": 2},
        {"quote": "Support is bad.", "theme": "Customer Support", "rating": 1},
        {"quote": "I like the new theme.", "theme": "UI/UX", "rating": 5}
      ],
      "action_ideas": [
        {"title": "Fix bugs", "rationale": "App crashes freq."},
        {"title": "Improve support", "rationale": "Bad support."},
        {"title": "UI changes", "rationale": "Keep it up."}
      ]
    }
    '''
    with patch.object(pulse_generator.client, "generate") as mock_generate:
        mock_generate.return_value = mock_json_response
        
        pulse = pulse_generator.generate_pulse(mock_reviews)
        
        assert "themes" in pulse
        assert "quotes" in pulse
        assert "actions" in pulse
        assert "meta" in pulse
        assert len(pulse["themes"]) == 3
        # Ensure only 1 LLM call is made
        assert mock_generate.call_count == 1

def test_generate_pulse_fallback(pulse_generator, mock_reviews):
    with patch.object(pulse_generator.client, "generate") as mock_generate:
        # Simulate invalid json
        mock_generate.return_value = "This is not JSON"
        
        pulse = pulse_generator.generate_pulse(mock_reviews)
        
        assert pulse["themes"][0]["name"] == "App Performance"
        assert pulse["quotes"][0]["quote"] == "Could not generate quotes due to API error."

def test_generate_pulse_no_themes(pulse_generator):
    pulse = pulse_generator.generate_pulse([])
    assert pulse["total_reviews"] == 0
    assert pulse["week_range"] == "N/A"

def test_run_phase5_end_to_end(pulse_generator, mock_reviews, tmp_path):
    input_path = tmp_path / "classified.json"
    output_path = tmp_path / "pulse.json"
    
    with open(input_path, "w", encoding="utf-8") as f:
        json.dump(mock_reviews, f)
        
    mock_json_response = '''
    {
      "top_themes": [],
      "user_quotes": [],
      "action_ideas": []
    }
    '''
    with patch.object(pulse_generator.client, "generate") as mock_generate:
        mock_generate.return_value = mock_json_response
        
        results = pulse_generator.run(str(input_path), str(output_path))
        
        assert output_path.exists()
        with open(output_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
            assert "meta" in saved_data
