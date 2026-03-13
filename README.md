<div align="center">

# 📊 INDMoney Weekly Pulse

**AI-powered Play Store review insights — pipeline, dashboard, and email — delivered automatically every week**

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org)
[![Groq](https://img.shields.io/badge/LLM-Groq%20LLaMA%203-F55036?logo=meta&logoColor=white)](https://groq.com)
[![Gemini](https://img.shields.io/badge/LLM-Gemini%202.5%20Flash-4285F4?logo=google&logoColor=white)](https://ai.google.dev)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React%2018-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![Docker](https://img.shields.io/badge/Docker-Containerised-2496ED?logo=docker&logoColor=white)](https://docker.com)
[![GitHub Actions](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white)](https://github.com/features/actions)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

<br/>

*Converts hundreds of raw user reviews into a one-page executive pulse + interactive dashboard — automatically, every week.*

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

A **full-stack AI platform** comprising:

1. **📥 Scrapes** recent Play Store reviews automatically
2. **🧹 Cleans** data and removes PII for privacy compliance
3. **🏷️ Discovers themes** using Groq LLaMA 3 (fast, cheap classification)
4. **📊 Generates a leadership-ready pulse** using Gemini 2.5 Flash (quality summaries)
5. **📧 Emails** a polished one-page report to stakeholders
6. **🖥️ Serves a REST API** via FastAPI for integrations
7. **🎨 Displays a React dashboard** with dark-mode, glassmorphism, and Recharts
8. **⏰ Runs weekly** via GitHub Actions — zero manual effort

### 📈 The Impact

| Metric | Before | After |
|--------|--------|-------|
| Time to read reviews | ~4 hours/week | **0 minutes** (automated) |
| Theme identification | Manual guesswork | **AI-generated, data-backed** |
| Leadership visibility | Ad-hoc, delayed | **Weekly email + live dashboard** |
| Actionable insights | Rare | **3 action ideas every week** |
| PII risk | High (raw reviews shared) | **Zero** (stripped in Phase 3) |
| Accessibility | CLI-only | **Web dashboard for anyone** |

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
                                            ┌──────────┐  ┌──────────┐
                                            │ Phase 7  │─▶│ Phase 8  │──▶ 🌐
                                            │ Backend  │  │ Frontend │
                                            │ (FastAPI)│  │(Dashboard│
                                            └──────────┘  └──────────┘
```

> **Phase 1** handles setup · **Phase 9** containerises with Docker · **Phase 10** schedules via GitHub Actions

📄 **Full architecture →** [`architecture/architecture.md`](architecture/architecture.md)

---

## 📁 10-Phase Project Structure

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
├── phase7_backend/                      # 🖥️ FastAPI REST API
├── phase8_frontend/                     # 🎨 React dashboard (Vite)
├── phase9_docker/                       # 🐳 Docker containerisation
├── phase10_scheduler/                   # ⏰ GitHub Actions cron scheduler
│
├── architecture/                        # 📐 System architecture docs
├── data/                                # 📂 Runtime outputs (gitignored)
│
├── .github/workflows/weekly_pulse.yml   # ⏰ Cron workflow
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
# Start the backend
uvicorn phase7_backend.app:app --port 8000

# In another terminal — start the React dev server
cd phase8_frontend
npm install && npm run dev
# Opens at http://localhost:5173 (proxies API to :8000)
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

# Server mode (dashboard)
docker run --env-file .env -p 8000:8000 weekly-pulse \
  uvicorn phase7_backend.app:app --host 0.0.0.0 --port 8000
```

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
| Theme Discovery | **Groq** | LLaMA 3 70B | Fast inference, cheap for classification |
| Review Classification | **Groq** | LLaMA 3 70B | Batch processing, low latency |
| Pulse Summarisation | **Gemini** | **2.5 Flash** | Superior reasoning, structured JSON, leadership-grade prose |
| Email Polish | **Gemini** | **2.5 Flash** | Professional language quality |

**Total: 4–5 LLM calls · ~30K tokens · ~$0.007 per run**

---

## 📬 Example Weekly Pulse Output

```
Subject: 📊 INDMoney Weekly User Pulse — Mar 06–13, 2026

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
| Theme Generation | Groq API (LLaMA 3 70B) |
| Summarisation | **Google Gemini 2.5 Flash** |
| Backend API | FastAPI + Uvicorn |
| Frontend | React 18, Vite, Recharts, CSS (dark mode) |
| Email Delivery | Gmail SMTP + Jinja2 |
| Containerisation | Docker |
| Scheduling | GitHub Actions (cron) |

---

## 📝 License

This project is built for educational and portfolio purposes.

---

<div align="center">

**Built with ❤️ as part of the GenAI Bootcamp**

</div>
