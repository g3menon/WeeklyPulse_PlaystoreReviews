import json
import logging
from datetime import datetime

from phase1_setup.config import (
    WEEKLY_PULSE_PATH,
    FEE_EXPLANATION_PATH,
    COMBINED_PULSE_PATH
)

logger = logging.getLogger("phase10b_json_combiner")

def run_json_combiner():
    try:
        with open(WEEKLY_PULSE_PATH, "r", encoding="utf-8") as f:
            pulse_data = json.load(f)
            
        fee_data = {}
        try:
            with open(FEE_EXPLANATION_PATH, "r", encoding="utf-8") as f:
                fee_data = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load fee data for combination: {e}")
            
        # Combine into the schema required
        
        # Extract themes
        themes_raw = pulse_data.get("themes", pulse_data.get("top_themes", []))
        themes = [t.get("name") for t in themes_raw]
        
        # Extract quotes
        quotes_raw = pulse_data.get("quotes", pulse_data.get("user_quotes", []))
        quotes = [q.get("text", q.get("quote")) for q in quotes_raw]
        
        # Extract actions
        actions_raw = pulse_data.get("actions", pulse_data.get("action_ideas", []))
        actions = [a.get("title") for a in actions_raw]
            
        combined_json = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "weekly_pulse": {
                "themes": themes,
                "quotes": quotes,
                "action_ideas": actions
            },
            "fee_scenario": fee_data.get("fee_scenario", "N/A"),
            "explanation_bullets": fee_data.get("explanation_bullets", []),
            "source_links": fee_data.get("source_links", []),
            "last_checked": fee_data.get("last_checked", datetime.now().strftime("%Y-%m-%d"))
        }
        
        with open(COMBINED_PULSE_PATH, "w", encoding="utf-8") as f:
            json.dump(combined_json, f, indent=2)
            
        logger.info(f"Successfully generated combined JSON at {COMBINED_PULSE_PATH}")
        
    except Exception as e:
        logger.error(f"Failed to combine JSONs: {e}")
        
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_json_combiner()
