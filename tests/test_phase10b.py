import os
import json
import pytest
from unittest.mock import patch

from phase10b_gdocs_mcp.json_combiner import run_json_combiner

def test_json_combiner(tmp_path):
    pulse_data = {
        "themes": [{"name": "Theme 1"}, {"name": "Theme 2"}],
        "quotes": [{"text": "Quote 1"}, {"text": "Quote 2"}],
        "actions": [{"title": "Action 1"}, {"title": "Action 2"}]
    }
    
    fee_data = {
        "fee_scenario": "Mutual Fund Exit Load",
        "explanation_bullets": ["Bullet 1", "Bullet 2"],
        "source_links": ["Link 1"],
        "last_checked": "2026-03-25"
    }

    weekly_pulse_file = tmp_path / "weekly_pulse.json"
    fee_explanation_file = tmp_path / "fee_explanation.json"
    combined_pulse_file = tmp_path / "combined_pulse.json"

    with open(weekly_pulse_file, "w", encoding="utf-8") as f:
        json.dump(pulse_data, f)
        
    with open(fee_explanation_file, "w", encoding="utf-8") as f:
        json.dump(fee_data, f)

    with patch('phase10b_gdocs_mcp.json_combiner.WEEKLY_PULSE_PATH', str(weekly_pulse_file)), \
         patch('phase10b_gdocs_mcp.json_combiner.FEE_EXPLANATION_PATH', str(fee_explanation_file)), \
         patch('phase10b_gdocs_mcp.json_combiner.COMBINED_PULSE_PATH', str(combined_pulse_file)):
        run_json_combiner()

    assert os.path.exists(combined_pulse_file)
    with open(combined_pulse_file, "r", encoding="utf-8") as f:
        combined_data = json.load(f)

    assert "date" in combined_data
    assert combined_data["weekly_pulse"]["themes"] == ["Theme 1", "Theme 2"]
    assert combined_data["weekly_pulse"]["quotes"] == ["Quote 1", "Quote 2"]
    assert combined_data["fee_scenario"] == "Mutual Fund Exit Load"

@patch('phase10b_gdocs_mcp.gdocs_appender.StdioServerParameters', True)
def test_gdocs_appender_graceful_failure(tmp_path):
    from phase10b_gdocs_mcp.gdocs_appender import run_mcp_appender_async
    import asyncio
    
    combined_pulse_file = tmp_path / "nonexistent.json"
    with patch('phase10b_gdocs_mcp.gdocs_appender.COMBINED_PULSE_PATH', str(combined_pulse_file)):
        with patch('phase10b_gdocs_mcp.gdocs_appender.logger') as mock_logger:
            asyncio.run(run_mcp_appender_async())
            mock_logger.error.assert_any_call("combined_pulse.json does not exist. Skipping MCP append.")
