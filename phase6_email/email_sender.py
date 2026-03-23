import json
import os
import logging
import smtplib
import ssl
from email.message import EmailMessage
from jinja2 import Environment, FileSystemLoader
from typing import Dict, Any

from phase1_setup.llm_clients import gemini_client
from phase1_setup.config import settings, WEEKLY_PULSE_PATH, EMAIL_DRAFT_PATH

logger = logging.getLogger("phase6_email")

class EmailSender:
    def __init__(self):
        self.client = gemini_client
        self.template_dir = os.path.join(os.path.dirname(__file__), "templates")
        
    def _polish_pulse_data(self, pulse_data: Dict[str, Any]) -> Dict[str, Any]:
        """Uses Gemini to polish the prose of the pulse data (Rule P6.1)."""
        prompt = f"""You are an executive communications specialist. I have generated a weekly pulse report for a fintech app from user reviews. Please polish the text to be professional, engaging, and suitable for the leadership team.
        
Here is the raw data in JSON format:
{json.dumps(pulse_data, indent=2)}

Please return the identical JSON structure, but refine the following fields for better flow and impact:
1. `explanation` in the `top_themes` (or `themes`) array.
2. `title` and `rationale` in the `action_ideas` (or `actions`) array.

Do not alter the review counts, ratings, quotes, numbers, or the overall JSON structure. 
Ensure valid JSON format and escape any necessary characters.
Return purely valid JSON with no introductory text and no markdown formatting (no ```json).
"""
        try:
            response_text = self.client.generate(prompt).strip()
            
            # clean up markdown backticks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:-3].strip()
                
            polished_data = json.loads(response_text)
            logger.info("Successfully polished pulse data with Gemini.")
            return polished_data
        except Exception as e:
            logger.error(f"Failed to polish pulse data, using raw data fallback. Error: {e}")
            return pulse_data  # Rule P6.6 Fallback

    def _prepare_template_context(self, pulse_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transforms pulse JSON into the context required by the Jinja2 template."""
        # Handle variations in keys
        themes_raw = pulse_data.get("top_themes", pulse_data.get("themes", []))
        quotes_raw = pulse_data.get("user_quotes", pulse_data.get("quotes", []))
        actions_raw = pulse_data.get("action_ideas", pulse_data.get("actions", []))
        meta = pulse_data.get("meta", {})
        
        # Format themes
        themes = []
        for t in themes_raw:
            themes.append({
                "name": t.get("name", "Unknown"),
                "count": t.get("review_count", 0),
                "avg_rating": t.get("avg_rating", 0.0),
                "explanation": t.get("explanation", "")
            })
            
        # Format quotes
        quotes = []
        for q in quotes_raw:
            text = q.get("quote", q.get("text", ""))
            quotes.append({
                "text": text,
                "rating": q.get("rating", 0),
                "theme": q.get("theme", "")
            })
            
        # Format actions (template expects list of strings)
        actions = []
        for a in actions_raw:
            title = a.get("title", "")
            rationale = a.get("rationale", "")
            if title and rationale:
                actions.append(f"<b>{title}</b> — {rationale}")
            elif title:
                actions.append(title)
            elif rationale:
                actions.append(rationale)
                
        # Calculate summary stats
        total_reviews = meta.get("total_reviews", pulse_data.get("total_reviews", 0))
        theme_count = len(themes)
        
        avg_rating = 0.0
        if themes:
            total_sum = sum(t["avg_rating"] * t["count"] for t in themes if t.get("count"))
            total_c = sum(t["count"] for t in themes if t.get("count"))
            if total_c > 0:
                avg_rating = round(total_sum / total_c, 1)

        week_range = meta.get("week_range", pulse_data.get("week_range", "Recent Week"))
        generated_at = pulse_data.get("generated_at", "")
        
        subject = f"📊 Weekly Pulse: INDMoney User Sentiment ({week_range})"
        
        return {
            "subject": subject,
            "total_reviews": total_reviews,
            "week_range": week_range,
            "avg_rating": avg_rating,
            "theme_count": theme_count,
            "themes": themes,
            "quotes": quotes,
            "actions": actions,
            "generated_at": generated_at,
            "rating_distribution": pulse_data.get("rating_distribution", None)
        }

    def render_email_html(self, context: Dict[str, Any]) -> str:
        """Renders the HTML email using Jinja2 (Rule P6.3)."""
        env = Environment(loader=FileSystemLoader(self.template_dir))
        template = env.get_template("email_template.html")
        return template.render(context)

    def save_draft(self, html_content: str, output_path: str):
        """Saves the HTML draft locally (Rule P6.2)."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        logger.info(f"Saved email draft to {output_path}")

    def send_smtp_email(self, html_content: str, subject: str):
        """Sends the email via Gmail SMTP."""
        email_address = settings.email_address
        email_password = settings.email_app_password
        
        if not email_address or not email_password:
            logger.error("EMAIL_ADDRESS or EMAIL_APP_PASSWORD not set. Cannot send email.")
            return

        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = email_address
        msg['To'] = email_address  # Sending to oneself
        
        msg.add_alternative(html_content, subtype='html')
        
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                server.login(email_address, email_password)
                server.send_message(msg)
            logger.info("Successfully sent weekly pulse email.")
        except Exception as e:
            logger.error(f"Failed to send email via SMTP: {e}")

    def run(self, input_path: str, draft_path: str):
        """Runs the Phase 6 pipeline."""
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
            
        with open(input_path, "r", encoding="utf-8") as f:
            pulse_data = json.load(f)
            
        polished_data = self._polish_pulse_data(pulse_data)
        context = self._prepare_template_context(polished_data)
        html_content = self.render_email_html(context)
        
        self.save_draft(html_content, draft_path)
        self.send_smtp_email(html_content, context["subject"])


def send_email():
    sender = EmailSender()
    sender.run(WEEKLY_PULSE_PATH, EMAIL_DRAFT_PATH)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    send_email()
