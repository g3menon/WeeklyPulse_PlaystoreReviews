import os
import json
import pytest
from unittest.mock import patch

try:
    from phase7_dashboard.app import load_data
except ImportError:
    load_data = None

@pytest.mark.skipif(load_data is None, reason="load_data could not be imported")
def test_load_data_files_exist(tmp_path):
    test_pulse = tmp_path / "weekly_pulse.json"
    test_pulse.write_text(json.dumps({"meta": {"total_reviews": 10}}))
    test_classified = tmp_path / "reviews_classified.json"
    test_classified.write_text(json.dumps([{"rating": 5}]))

    with patch("phase7_dashboard.app.PULSE_FILE", str(test_pulse)), \
         patch("phase7_dashboard.app.CLASSIFIED_FILE", str(test_classified)):
        
        pulse_data, classified_data = load_data()
        assert pulse_data is not None
        assert classified_data is not None
        assert pulse_data["meta"]["total_reviews"] == 10
        assert len(classified_data) == 1

@pytest.mark.skipif(load_data is None, reason="load_data could not be imported")
def test_load_data_files_missing():
    with patch("phase7_dashboard.app.PULSE_FILE", "some_nonexistent_file.json"), \
         patch("phase7_dashboard.app.CLASSIFIED_FILE", "some_other_nonexistent_file.json"):
        pulse_data, classified_data = load_data()
        assert pulse_data is None
        assert classified_data is None
