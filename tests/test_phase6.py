import os
import json
import pytest
from unittest.mock import patch, MagicMock
from phase6_email.email_sender import EmailSender

@pytest.fixture
def mock_pulse_data():
    return {
        "top_themes": [
            {
                "name": "App Performance",
                "review_count": 10,
                "avg_rating": 2.5,
                "explanation": "Users are complaining about app crashes."
            }
        ],
        "user_quotes": [
            {
                "text": "The app crashed while making a transaction.",
                "rating": 1,
                "theme": "App Performance"
            }
        ],
        "action_ideas": [
            {
                "title": "Fix Crashes",
                "rationale": "App crashes are the leading cause of 1-star reviews."
            }
        ],
        "meta": {
            "total_reviews": 100,
            "week_range": "Mar 01 - Mar 08"
        }
    }

class TestPhase6:
    @patch("phase6_email.email_sender.gemini_client.generate")
    def test_polish_pulse_data(self, mock_generate, mock_pulse_data):
        mock_generate.return_value = json.dumps(mock_pulse_data)
        
        sender = EmailSender()
        polished_data = sender._polish_pulse_data(mock_pulse_data)
        
        assert "App Performance" in json.dumps(polished_data)
        mock_generate.assert_called_once()
        
    def test_prepare_template_context(self, mock_pulse_data):
        sender = EmailSender()
        context = sender._prepare_template_context(mock_pulse_data)
        
        assert context["total_reviews"] == 100
        assert context["week_range"] == "Mar 01 - Mar 08"
        assert context["theme_count"] == 1
        assert context["themes"][0]["name"] == "App Performance"
        assert len(context["quotes"]) == 1
        assert context["actions"][0] == "<b>Fix Crashes</b> — App crashes are the leading cause of 1-star reviews."

    @patch("phase6_email.email_sender.os.makedirs")
    @patch("builtins.open", new_callable=MagicMock)
    def test_save_draft(self, mock_open, mock_makedirs):
        sender = EmailSender()
        sender.save_draft("<html></html>", "dummy_path.html")
        mock_open.assert_called_once()

    @patch("phase6_email.email_sender.smtplib.SMTP_SSL")
    def test_send_smtp_email(self, mock_smtp):
        with patch("phase6_email.email_sender.settings.email_address", "test@example.com"), \
             patch("phase6_email.email_sender.settings.email_app_password", "password"):
            sender = EmailSender()
            sender.send_smtp_email("<html></html>", "Test Subject")
            
            mock_smtp.assert_called_once()
