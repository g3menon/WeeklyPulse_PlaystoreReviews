<div align="center">

# 📊 INDMoney Weekly Pulse

**AI-powered Play Store review insights — pipeline, dashboard, and email — delivered automatically every week**

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org)
[![Groq](https://img.shields.io/badge/LLM-Groq%20LLaMA%203.3-F55036?logo=meta&logoColor=white)](https://groq.com)
[![Gemini](https://img.shields.io/badge/LLM-Gemini%202.5%20Flash-4285F4?logo=google&logoColor=white)](https://ai.google.dev)
[![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Docker](https://img.shields.io/badge/Docker-Containerised-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![GitHub Actions](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white)](https://github.com/features/actions)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

<br/>

*Converts hundreds of raw user reviews into a one-page executive pulse + interactive Streamlit dashboard — automatically, every week.*

</div>

---

## 🧠 Problem → Solution → Impact

### ❌ The Problem

Product teams at fintech companies like INDMoney receive **hundreds of Play Store reviews every week**. But:

- Nobody has time to read them all
- Patterns get buried in noise
- Critical issues surface too late
- Leadership lacks a quick "pulse check" on user sentiment
- There's no visual dashboard to explore trends

### ✅ The Solution

An **AI-powered insights platform** comprising:

1. **📥 Scrapes** recent Play Store reviews automatically
2. **🧹 Cleans** data and removes PII for privacy compliance
3. **🏷️ Discovers themes** using Groq LLaMA 3.3 (fast, cheap classification)
4. **📊 Generates a leadership-ready pulse** using Gemini 2.5 Flash (quality summaries)
5. **📧 Emails** a polished one-page report to stakeholders
6. **📊 Displays a Streamlit dashboard** with charts, filters, and interactive data
7. **⏰ Runs weekly** via GitHub Actions — zero manual effort

### 📈 The Impact

| Metric | Before | After |
|--------|--------|-------|
| Time to read reviews | ~4 hours/week | **0 minutes** (automated) |
| Theme identification | Manual guesswork | **AI-generated, data-backed** |
| Leadership visibility | Ad-hoc, delayed | **Weekly email + live dashboard** |
| Actionable insights | Rare | **3 action ideas every week** |
| PII risk | High (raw reviews shared) | **Zero** (stripped in Phase 3) |
| Dashboard access | None | **Streamlit Cloud (free, shareable)** |

---

## 🏗️ System Architecture

```
  Google Play Store
        │
        ▼
  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │ Phase 2  │─▶│ Phase 3  │─▶│ Phase 4  │─▶│ Phase 5  │─▶│ Phase 6  │──▶ 📧
  │ Scrape   │  │ Clean    │  │ Themes   │  │ Pulse    │  │ Email    │
  │          │  │ PII Strip│  │ (Groq)   │  │(Gemini)  │  │ (Gmail)  │
  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘
                                                  │
                                                  ▼
                                          ┌──────────────┐
                                          │   Phase 7    │──▶ 🌐
                                          │  Streamlit   │
                                          │  Dashboard   │
                                          └──────────────┘
```

> **Phase 1** handles setup · **Phase 8** containerises with Docker · **Phase 9** schedules via GitHub Actions

📄 **Full architecture →** [`architecture/architecture.md`](architecture/architecture.md)

---

## 📁 9-Phase Project Structure

```
WeeklyPulse_PlaystoreReviews/
│
├── main.py                              # 🚀 Pipeline orchestrator
│
├── phase1_setup/                        # ⚙️ Config, logging, LLM clients
├── phase2_scraper/                      # 📥 Play Store review scraping
├── phase3_cleaning/                     # 🧹 PII removal & normalisation
├── phase4_themes/                       # 🏷️ Groq-powered theme generation
├── phase5_pulse/                        # 📊 Gemini 2.5 Flash pulse summary
├── phase6_email/                        # 📧 Email drafting & SMTP delivery
├── phase7_dashboard/                    # 📊 Streamlit interactive dashboard
├── phase8_docker/                       # 🐳 Docker containerisation
├── phase9_scheduler/                    # ⏰ GitHub Actions cron scheduler
│
├── architecture/                        # 📐 System architecture docs
├── tests/                               # 🧪 Test suites
├── data/                                # 📂 Runtime outputs (gitignored)
│
├── .github/workflows/weekly_pulse.yml   # ⏰ Cron workflow
├── .streamlit/config.toml               # 🎨 Streamlit theme
├── Dockerfile                           # 🐳 Container definition
├── .env.example                         # 🔐 Env var template
├── requirements.txt                     # 📦 Python dependencies
└── README.md                            # 📖 You are here
```

> Each phase folder contains its own **README.md** with purpose, diagrams, inputs/outputs, and how to run.

---

## ⚡ Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/<your-username>/WeeklyPulse_PlaystoreReviews.git
cd WeeklyPulse_PlaystoreReviews
python -m venv venv && venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys and Gmail credentials
```

### 3. Run the Pipeline

```bash
python main.py
# Runs: Scrape → Clean → Themes → Pulse → Email
```

### 4. Launch the Dashboard

```bash
streamlit run phase7_dashboard/app.py
# Opens at http://localhost:8501
```

---

## 🔐 Environment Variables

| Variable | Purpose | Where to Get |
|----------|---------|--------------|
| `GROQ_API_KEY` | Theme generation & classification | [console.groq.com](https://console.groq.com) |
| `GEMINI_API_KEY` | Pulse summaries & email polish | [ai.google.dev](https://ai.google.dev) |
| `EMAIL_ADDRESS` | Gmail sender & recipient | Your Gmail address |
| `EMAIL_APP_PASSWORD` | Gmail SMTP authentication | [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) |

---

## 🐳 Running with Docker

```bash
# Build
docker build -t weekly-pulse .

# Pipeline mode (scrape → email)
docker run --env-file .env weekly-pulse

# Dashboard mode
docker run --env-file .env -p 8501:8501 weekly-pulse \
  streamlit run phase7_dashboard/app.py --server.port 8501 --server.address 0.0.0.0
```

---

## 🌐 Deploy on Streamlit Cloud (Free)

1. Push repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Select your repo → `phase7_dashboard/app.py`
4. Add secrets in Streamlit Cloud dashboard
5. Deploy!

---

## ⏰ Automated Scheduling

The pipeline runs **every Monday at 9 AM UTC** via GitHub Actions.

```yaml
on:
  schedule:
    - cron: '0 9 * * 1'
```

Add your secrets in **GitHub → Settings → Secrets → Actions**.

---

## 🤖 LLM Strategy

| Task | Provider | Model | Why |
|------|----------|-------|-----|
| Theme Discovery | **Groq** | LLaMA 3.3 70B | Fast inference, cheap for classification |
| Review Classification | **Groq** | LLaMA 3.3 70B | Batch processing, low latency |
| Pulse Summarisation | **Gemini** | **2.5 Flash** | Superior reasoning, structured JSON, leadership-grade prose |
| Email Polish | **Gemini** | **2.5 Flash** | Professional language quality |

**Total: 4–5 LLM calls · ~30K tokens · ~$0.007 per run**

---

## 📬 Example Weekly Pulse Output

```
Subject: 📊 INDMoney Weekly User Pulse — Mar 13–18, 2026

Hi Team,

Here's your weekly user sentiment pulse based on 187 Play Store
reviews from the past week.

── TOP THEMES ──────────────────────────────────────────

1. App Performance (47 reviews, ★2.3)
   Users report frequent crashes during portfolio loading
   and slow app startup times, especially on older devices.

2. Investment Features (38 reviews, ★3.8)
   Positive reception for new SIP tracking, but users
   request better mutual fund comparison tools.

3. Customer Support (32 reviews, ★2.1)
   Delayed responses to in-app support queries.
   Users cite 3–5 day wait times.

── WHAT USERS ARE SAYING ───────────────────────────────

💬 "The app freezes every time I try to check my portfolio.
    I've reinstalled it twice already." (★2)

💬 "Love the SIP tracker! Would be great if I could
    compare funds side by side." (★4)

💬 "Raised a ticket 4 days ago, still no response.
    Very disappointing for a financial app." (★1)

── SUGGESTED ACTIONS ───────────────────────────────────

→ Optimise cold-start latency and portfolio loading
→ Add mutual fund comparison feature to investment dashboard
→ Implement SLA-based support ticket escalation

Best,
Weekly Pulse Bot
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11 |
| Review Scraping | `google-play-scraper` |
| Data Cleaning | Regex + custom PII filters |
| Theme Generation | Groq API (LLaMA 3.3 70B) |
| Summarisation | **Google Gemini 2.5 Flash** |
| Dashboard | **Streamlit** + Plotly |
| Email Delivery | Gmail SMTP + Jinja2 |
| Containerisation | Docker |
| Scheduling | GitHub Actions (cron) |
| Deployment | **Streamlit Cloud** (free) |

---

## 📝 License

This project is built for educational and portfolio purposes.

---

<div align="center">

**Built with ❤️ as part of the GenAI Bootcamp**

</div>
