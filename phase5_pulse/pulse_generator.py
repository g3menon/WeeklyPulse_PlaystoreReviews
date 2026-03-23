import json
import os
import logging
from datetime import datetime
from typing import Dict, List, Any

from phase1_setup.llm_clients import gemini_client

logger = logging.getLogger("phase5_pulse")

class PulseGenerator:
    def __init__(self):
        self.client = gemini_client

    def generate_pulse(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generates the pulse summary from classified reviews using Gemini.
        """
        # Step 1: Aggregate stats per theme
        theme_stats = {}
        for rev in reviews:
            for theme in rev.get("themes", []):
                if theme not in theme_stats:
                    theme_stats[theme] = {"count": 0, "sum_rating": 0}
                theme_stats[theme]["count"] += 1
                theme_stats[theme]["sum_rating"] += rev.get("rating", 0)

        # Step 2: Rank themes by review count
        ranked_themes = []
        for theme, stats in theme_stats.items():
            avg_rating = stats["sum_rating"] / stats["count"]
            ranked_themes.append({
                "name": theme,
                "review_count": stats["count"],
                "avg_rating": round(avg_rating, 1)
            })
        
        ranked_themes.sort(key=lambda x: x["review_count"], reverse=True)
        top_3_themes = ranked_themes[:3]

        if not top_3_themes:
            logger.warning("No themes found in classified reviews.")
            return self._fallback_pulse(reviews)

        # Step 3: Single Gemini 2.5 Flash call
        prompt = self._build_prompt(reviews, top_3_themes)
        
        try:
            response_text = self.client.generate(prompt)
            # Try parsing the JSON
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:-3].strip()
            elif cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:-3].strip()
            
            pulse_data = json.loads(cleaned_text)
            
            # Validate and Enrich
            self._enrich_pulse_data(pulse_data, reviews, top_3_themes)
            return pulse_data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON from Gemini: {e}\nResponse: {response_text}")
            logger.info("Falling back to basic aggregation summary.")
            return self._fallback_pulse(reviews, top_3_themes)
        except Exception as e:
            logger.error(f"Failed to generate pulse: {e}")
            logger.info("Falling back to basic aggregation summary.")
            return self._fallback_pulse(reviews, top_3_themes)

    def _build_prompt(self, reviews: List[Dict[str, Any]], top_3_themes: List[Dict[str, Any]]) -> str:
        theme_names = [t["name"] for t in top_3_themes]
        
        relevant_reviews = []
        for rev in reviews:
            rev_themes = set(rev.get("themes", []))
            if rev_themes.intersection(set(theme_names)):
                relevant_reviews.append({
                    "text": rev.get("text", ""),
                    "rating": rev.get("rating", 0),
                    "themes": rev.get("themes", [])
                })
        
        limited_reviews = relevant_reviews[:100]

        prompt = f"""You are a senior product analyst at a fintech company.

I am providing you with {len(reviews)} recent app reviews and their classification into themes.
The top 3 themes by volume are:
{json.dumps(top_3_themes, indent=2)}

Here are some of the reviews:
{json.dumps(limited_reviews, indent=2)}

Based on these reviews, please generate a structured JSON object containing a weekly pulse report for the leadership team.
The output MUST be valid JSON, conforming strictly to the following schema, and be concise (under 1,500 tokens).

Required JSON Schema:
{{
  "top_themes": [
    {{
      "rank": <integer>,
      "name": "<string>",
      "review_count": <integer>,
      "avg_rating": <float>,
      "explanation": "<string (concise explanation of what users are saying under this theme)>"
    }}
  ],
  "user_quotes": [
    {{
      "quote": "<string (extract 3 impactful, fully anonymised quotes)>",
      "theme": "<string>",
      "rating": <integer>
    }}
  ],
  "action_ideas": [
    {{
      "title": "<string (short action idea)>",
      "rationale": "<string (why this matters based on reviews)>"
    }}
  ]
}}

Rules:
1. "top_themes" should exactly contain the 3 themes provided, with an "explanation" derived from the reviews. Use the review_count and avg_rating values I gave you.
2. "user_quotes" must contain exactly 3 quotes. ANONYMISE the quotes (do not include names, specific account amounts like '5L', phone numbers, email IDs, or highly specific personal info).
3. "action_ideas" must contain exactly 3 actionable improvements.
4. ONLY return valid JSON. Do not include introductory text or Markdown formatting around the JSON (no ```json).
5. Ensure valid JSON format (escape necessary characters).
"""
        return prompt

    def _fallback_pulse(self, reviews: List[Dict[str, Any]], top_3_themes: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generates a fallback pulse object if LLM fails."""
        if not top_3_themes:
            top_3_themes = []
        
        pulse_data = {
            "top_themes": [
                {
                    "rank": i + 1,
                    "name": t.get("name", "Unknown"),
                    "review_count": t.get("review_count", 0),
                    "avg_rating": t.get("avg_rating", 0.0),
                    "explanation": "Could not generate explanation due to API error."
                } for i, t in enumerate(top_3_themes)
            ],
            "user_quotes": [
                {
                    "quote": "Could not generate quotes due to API error.",
                    "theme": "N/A",
                    "rating": 0
                }
            ],
            "action_ideas": [
                {
                    "title": "Review API integration",
                    "rationale": "Automated action idea. The LLM generation failed for this pulse."
                }
            ]
        }
        self._enrich_pulse_data(pulse_data, reviews, top_3_themes)
        return pulse_data

    def _enrich_pulse_data(self, pulse_data: Dict[str, Any], reviews: List[Dict[str, Any]], top_3_themes: List[Dict[str, Any]]):
        if reviews and "date" in reviews[0]:
            try:
                dates = [datetime.strptime(r["date"], "%Y-%m-%d") for r in reviews if "date" in r]
                if dates:
                    min_date = min(dates)
                    max_date = max(dates)
                    week_range = f"{min_date.strftime('%b %d')} – {max_date.strftime('%b %d, %Y')}"
                else:
                    week_range = "N/A"
            except Exception:
                week_range = "N/A"
        else:
            week_range = "N/A"

        pulse_data["generated_at"] = datetime.now().isoformat()
        pulse_data["week_range"] = week_range
        pulse_data["total_reviews"] = len(reviews)
        
        if "top_themes" in pulse_data and "themes" not in pulse_data:
            pulse_data["themes"] = pulse_data["top_themes"]
        if "user_quotes" in pulse_data and "quotes" not in pulse_data:
            pulse_data["quotes"] = pulse_data["user_quotes"]
        if "action_ideas" in pulse_data and "actions" not in pulse_data:
            pulse_data["actions"] = pulse_data["action_ideas"]
            
        pulse_data["meta"] = {
            "total_reviews": len(reviews),
            "week_range": week_range
        }
        
    def run(self, input_path: str, output_path: str) -> Dict[str, Any]:
        """Runs Phase 5 pipeline."""
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
            
        with open(input_path, "r", encoding="utf-8") as f:
            reviews = json.load(f)
            
        pulse_data = self.generate_pulse(reviews)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(pulse_data, f, indent=2)
            
        logger.info(f"Phase 5 complete. Saved pulse to {output_path}")
        return pulse_data

def generate_pulse():
    generator = PulseGenerator()
    generator.run("data/reviews_classified.json", "data/weekly_pulse.json")

if __name__ == "__main__":
    generate_pulse()
