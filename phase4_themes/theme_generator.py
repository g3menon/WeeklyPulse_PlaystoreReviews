import json
import re
from typing import List, Dict, Any

from phase1_setup.llm_clients import groq_client
from phase1_setup.logger import get_logger

logger = get_logger("phase4_themes")

class ThemeGenerator:
    """
    Phase 4: Generate themes and classify reviews using Groq (LLaMA 3).
    """

    def __init__(self):
        self.client = groq_client

    def _extract_json(self, response_text: str) -> Any:
        """Helper to extract JSON from LLM response."""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to find JSON block
            match = re.search(r"```(?:json)?\s*(.*?)\s*```", response_text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
            # If still fails, try to find array or object
            match = re.search(r"(\[.*\]|\{.*\})", response_text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
            
            raise ValueError(f"Could not parse JSON from response: {response_text}")

    def discover_themes(self, reviews: List[Dict[str, Any]]) -> List[str]:
        """
        Step 1: Discover 3-5 product-related themes from the reviews.
        """
        if not reviews:
            return []

        # Prepare review data for prompt (minimize tokens)
        reviews_text = "\n".join([f"- {r['text']}" for r in reviews])
        
        system_prompt = "You are an expert product analyst."
        prompt = f"""Given these {len(reviews)} reviews, identify between 5 and 7 distinct product-related themes.
At least one of these themes MUST explicitly cover positive feedback, good experiences, or what is working well.
Output the result strictly as a JSON array of strings containing the theme names.
Do not include any other text, markdown formatting, or explanations. Just the JSON array.

Reviews:
{reviews_text}"""
        
        logger.info("Discovering themes from reviews via Groq...")
        
        # Rule P4.4: Limit themes to 3-5. Retry once if fails.
        for attempt in range(2):
            try:
                # Rule P4.6: Use temperature = 0 for classification tasks.
                # Here we use 0.0 although it's discovery, maybe slightly higher? But rules say:
                # "Use temperature = 0 for classification tasks." Let's use 0.0 for all Phase 4 if possible.
                response = self.client.chat(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=0.0
                )
                
                themes = self._extract_json(response)
                
                if isinstance(themes, dict) and 'themes' in themes:
                    themes = themes['themes']
                    
                if not isinstance(themes, list):
                    raise ValueError("Expected JSON array of themes")
                
                themes = [str(t) for t in themes]
                
                if 5 <= len(themes) <= 7:
                    logger.info(f"Discovered {len(themes)} themes: {themes}")
                    return themes
                else:
                    logger.warning(f"Attempt {attempt+1}: Found {len(themes)} themes, expected 5-7. Retrying...")
            except Exception as e:
                logger.warning(f"Attempt {attempt+1}: Failed to generate themes: {e}")
        
        # If it still fails, use the raw response / last parsed list and log warning
        try:
            if 'themes' in locals() and isinstance(themes, list) and len(themes) > 0:
                logger.warning(f"Using parsed {len(themes)} themes despite failing 5-7 limit.")
                return themes[:7] # cap at 7
        except Exception:
            pass
            
        default_themes = ["App Performance", "User Interface", "Features", "Customer Support", "Pricing", "Positive Experience"]
        logger.warning(f"Falling back to default themes: {default_themes}")
        return default_themes

    def classify_reviews(self, reviews: List[Dict[str, Any]], themes: List[str]) -> List[Dict[str, Any]]:
        """
        Step 2: Classify reviews into the discovered themes.
        Batch processing rule P4.2.
        """
        if not reviews or not themes:
            return reviews
            
        # We need to batch. 1-2 calls allowed. We have max 200 reviews. 
        # We can split into 2 batches of 100 if we want to be safe with token limits, 
        # but 200 reviews of ~30 words should easily fit in LLaMA 3.3 70B's context window.
        # Let's try to do it in 1 call, fallback to 2 calls? Rule P4.1: Batch classification = 1-2 calls.
        
        # We will split into max 2 batches to ensure we don't exceed max_tokens in output.
        # {review_id: theme} max 200 items in JSON -> ~200 * (15 + 15) = 6000 chars -> ~1500 tokens. Output fits.
        
        batch_size = 100
        batches = [reviews[i:i + batch_size] for i in range(0, len(reviews), batch_size)]
        
        classified_reviews = list(reviews) # Copy
        review_dict = {r['review_id']: r for r in classified_reviews}
        
        system_prompt = "You are an expert product analyst. Always output perfectly valid JSON without backticks or markdown."
        
        for i, batch in enumerate(batches):
            logger.info(f"Classifying batch {i+1}/{len(batches)} ({len(batch)} reviews)...")
            
            # Prepare minimal data for classification
            batch_data = [{"id": r['review_id'], "text": r['text']} for r in batch]
            
            prompt = f"""Classify each review into one or more of these themes:
{json.dumps(themes)}

IMPORTANT RULES:
1. Ensure accurate sentiment classification: do not map positive feedback to negative themes (e.g., if a user praises support after a crash, include a positive theme like "Positive Experience" or "Great Support", not just "App Performance" or "Poor Support").
2. A single review can be associated with multiple themes if it touches on several distinct topics.

Output a valid JSON object mapping the review 'id' directly to an array of 'theme' names. 
Example format:
{{
  "id1": ["Theme1", "Theme2"],
  "id2": ["Theme3"]
}}

Reviews to classify:
{json.dumps(batch_data)}
"""
            try:
                # Rule P4.6: temperature = 0
                response = self.client.chat(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=0.0
                )
                
                classifications = self._extract_json(response)
                
                if not isinstance(classifications, dict):
                    logger.warning(f"Classification result is not a dictionary. Attempting to fix.")
                    continue
                    
                # Merge labels
                for review_id, assigned_themes in classifications.items():
                    if review_id in review_dict:
                        if isinstance(assigned_themes, str):
                            assigned_themes = [assigned_themes]
                        if isinstance(assigned_themes, list):
                            review_dict[review_id]['themes'] = [t for t in assigned_themes if t in themes]
                        
            except Exception as e:
                logger.error(f"Failed to classify batch {i+1}: {e}")
                # Fallback: assign a default theme if API fails
                for r in batch:
                    if r['review_id'] in review_dict:
                        review_dict[r['review_id']]['themes'] = [themes[0]] # Default to first theme
        
        # Ensure all reviews have a theme
        for r in classified_reviews:
            if 'themes' not in r or not r['themes']:
                r['themes'] = [themes[0]] if themes else ["Uncategorized"]
                
        return classified_reviews

    def run(self, cleaned_reviews_path: str, output_path: str):
        """
        Main runner for Phase 4.
        """
        logger.info("Starting Phase 4: Theme Generation & Classification")
        
        with open(cleaned_reviews_path, 'r', encoding='utf-8') as f:
            reviews = json.load(f)
            
        logger.info(f"Loaded {len(reviews)} cleaned reviews.")
        
        themes = self.discover_themes(reviews)
        classified_reviews = self.classify_reviews(reviews, themes)
        
        # Save output
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(classified_reviews, indent=2, ensure_ascii=False))
            
        logger.info(f"Saved {len(classified_reviews)} classified reviews to {output_path}")
        logger.info("Phase 4 completed successfully.")
        return classified_reviews

def run_theme_generation():
    from phase1_setup.config import REVIEWS_CLEANED_PATH, REVIEWS_CLASSIFIED_PATH
    generator = ThemeGenerator()
    generator.run(str(REVIEWS_CLEANED_PATH), str(REVIEWS_CLASSIFIED_PATH))
