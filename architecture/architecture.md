# 🏗️ INDMoney Weekly Pulse — System Architecture

> Complete architectural reference for the AI-powered Play Store review insights platform.

---

## 1. High-Level System Overview

The system is a **9-phase core pipeline + 2 enhancement features (10A, 10B) + Streamlit dashboard** that converts raw Google Play Store reviews into a polished weekly product-health report, enriched with mutual fund fee explanations and archived to Google Docs via MCP. No message queues, no complex orchestration — just clean, phase-based execution.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                      WEEKLY PULSE PLATFORM                                   │
│                                                                                              │
│  DATA PIPELINE                                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Phase 1  │─▶│ Phase 2  │─▶│ Phase 3  │─▶│ Phase 4  │─▶│ Phase 5  │─▶│ Phase 6  │        │
│  │ Setup    │  │ Scrape   │  │ Clean    │  │ Themes   │  │ Pulse    │  │ Email    │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│       │            │            │             │              │              │                 │
│    .env        Play Store    Regex/NLP     Groq API     Gemini 2.5     Gmail SMTP            │
│                                            LLaMA 3.3     Flash                               │
│                                                                                              │
│  DASHBOARD                                   ENHANCEMENTS                                    │
│  ┌──────────────────────┐                  ┌──────────────┐  ┌──────────────┐              │
│  │     Phase 7          │                  │  Phase 10A   │  │  Phase 10B   │              │
│  │  Streamlit Dashboard │                  │  Fee Explain │  │  Google Docs  │             │
│  │  (reads data/*.json) │                  │  (Exit Load) │  │  (MCP)       │             │
│  └──────────────────────┘                  └──────────────┘  └──────────────┘              │
│           │                                      │                   │                       │
│      http://localhost:8501                   indmoney.com      Google Docs API               │
│                                                                                              │
│  DEPLOYMENT                                                                                  │
│  ┌──────────┐  ┌──────────┐                                                                  │
│  │ Phase 8  │  │ Phase 9  │                                                                  │
│  │ Docker   │  │ Scheduler│                                                                  │
│  └──────────┘  └──────────┘                                                                  │
│       │              │                                                                       │
│   Container     GitHub Actions                                                               │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

> 📏 **Governance:** All phases are bound by the rules defined in [`rules.md`](../rules.md).
> Rules are segregated by phase and cover data quality, PII handling, cost control, and deployment hygiene.

---

## 2. Phase Map

| Phase | Folder | Purpose | Technology | Depends On |
|-------|--------|---------|------------|------------|
| **1** | `phase1_setup/` | Project config, env vars, logging, LLM clients | python-dotenv | — |
| **2** | `phase2_scraper/` | Scrape Play Store reviews | google-play-scraper | Phase 1 |
| **3** | `phase3_cleaning/` | PII removal & data normalisation | Regex (stdlib) | Phase 2 |
| **4** | `phase4_themes/` | Theme discovery + review classification | **Groq** (LLaMA 3.3 70B) | Phase 3 |
| **5** | `phase5_pulse/` | Generate weekly pulse summary | **Gemini 2.5 Flash** | Phase 4 |
| **6** | `phase6_email/` | Draft HTML email & send via Gmail | **Gemini 2.5 Flash** + SMTP | Phase 5, 10A |
| **7** | `phase7_dashboard/` | Interactive Streamlit dashboard | **Streamlit** + Plotly | Phase 5 |
| **8** | `phase8_docker/` | Docker containerisation | Docker | All |
| **9** | `phase9_scheduler/` | GitHub Actions cron automation | GitHub Actions | Phase 8 |
| **10A** | `phase10_fee_explainer/` | Scrape mutual fund exit load & append to email | requests + BeautifulSoup | Phase 5 |
| **10B** | `phase10_gdocs_mcp/` | Append combined JSON to Google Docs via MCP | MCP (Google Docs) | Phase 5, 10A |

---

## 3. Data Flow Diagram

```mermaid
flowchart TD
    A["Google Play Store"] -->|google-play-scraper| B["Phase 2: Scrape"]
    B -->|reviews_raw.json| C["Phase 3: Clean"]
    C -->|reviews_cleaned.json| D["Phase 4: Themes"]
    D -->|"Groq API (LLaMA 3.3)"| D
    D -->|reviews_classified.json| E["Phase 5: Pulse"]
    E -->|"Gemini 2.5 Flash"| E
    E -->|weekly_pulse.json| F["Phase 6: Email"]
    E -->|weekly_pulse.json| G["Phase 7: Streamlit Dashboard"]
    F -->|"Gemini 2.5 Flash + SMTP"| H["Developer Inbox"]
    G -->|"Browser :8501"| I["User Views Dashboard"]

    style A fill:#4285F4,color:#fff
    style D fill:#F97316,color:#fff
    style E fill:#8B5CF6,color:#fff
    style F fill:#10B981,color:#fff
    style G fill:#FF4B4B,color:#fff
    style H fill:#EF4444,color:#fff
    style I fill:#06B6D4,color:#fff
```

### File-Based Data Flow

```
data/
├── reviews_raw.json          ← Phase 2 writes  → Phase 3 reads
├── reviews_cleaned.json      ← Phase 3 writes  → Phase 4 reads
├── reviews_classified.json   ← Phase 4 writes  → Phase 5 reads, Phase 7 reads
├── weekly_pulse.json         ← Phase 5 writes  → Phase 6, 7, 10B read
├── fee_explanation.json      ← Phase 10A writes → Phase 6, 10B read
├── combined_pulse.json       ← Phase 10B writes → Google Docs (MCP append)
└── email_draft.html          ← Phase 6 writes  (also sends email)
```

---

## 4. Phase-Wise Deep Dive

### Phase 1 — Setup & Configuration

```
Responsibility:
  ├── Load environment variables from .env via python-dotenv
  ├── Initialise Groq client wrapper
  ├── Initialise Gemini 2.5 Flash client wrapper
  ├── Configure structured logging with timestamps
  ├── Export shared constants:
  │     APP_ID = "in.indwealth"
  │     DATE_WINDOW_WEEKS = 8
  │     MAX_REVIEWS = 200
  │     GROQ_MODEL = "llama-3.3-70b-versatile"
  │     GEMINI_MODEL = "gemini-2.5-flash"
  └── Validate all required env vars exist on startup
```

**Folder:** `phase1_setup/`
**Files:** `config.py`, `llm_clients.py`, `logger.py`, `__init__.py`
**Pipeline entry:** `main.py` (repo root) — scaffolded, phases uncomment as built
**Status:** ✅ Implemented & Tested (6/6 tests pass) · README updated · All rules P1.1–P1.3 met

---

### Phase 2 — Review Scraping

```
Input:  App ID (in.indwealth)
Output: data/reviews_raw.json

Flow:
  google-play-scraper.reviews()
        │
        ▼
  Sort by NEWEST, fetch up to 1000
        │
        ▼
  Filter: date >= (today - 8 weeks)
        │
        ▼
  Deduplicate by review_id
        │
        ▼
  Cap at 200 reviews for LLM cost control
        │
        ▼
  Save → data/reviews_raw.json

Schema per review:
  {
    review_id, rating (1-5), title, text,
    date (YYYY-MM-DD), thumbs_up
  }
```

**Folder:** `phase2_scraper/`
**Files:** `scraper.py`

---

### Phase 3 — Data Cleaning & PII Removal

```
Input:  data/reviews_raw.json
Output: data/reviews_cleaned.json

Flow:
  Load raw reviews
        │
        ▼
  Regex PII stripping:
    ├── Emails:    [\w.-]+@[\w.-]+\.\w+  →  [EMAIL]
    ├── Phones:    \+?\d[\d\s-]{7,}\d    →  [PHONE]
    └── Aadhaar:   \d{4}\s?\d{4}\s?\d{4} →  [ID]
        │
        ▼
  Normalise whitespace, fix encoding
        │
        ▼
  Remove reviews with < 10 chars of text
        │
        ▼
  Save → data/reviews_cleaned.json
```

**Folder:** `phase3_cleaning/`
**Files:** `cleaner.py`

---

### Phase 4 — Theme Generation & Classification (Groq)

```
Input:  data/reviews_cleaned.json
Output: data/reviews_classified.json
LLM:    Groq API — LLaMA 3.3 70B (llama-3.3-70b-versatile)

Step 1 — Theme Discovery (1 LLM call)
  ┌──────────────────────────────────────────┐
  │  System: You are a product analyst.      │
  │  Prompt: Given these 200 reviews,        │
  │  identify 3-5 product-related themes.    │
  │  Output: JSON array of theme names       │
  └──────────────────────────────────────────┘
              │
              ▼
Step 2 — Batch Classification (1-2 LLM calls)
  ┌──────────────────────────────────────────┐
  │  Prompt: Classify each review into one   │
  │  of these themes: [Theme1, Theme2, ...]  │
  │  Output: {review_id: theme} mapping      │
  └──────────────────────────────────────────┘
              │
              ▼
  Merge theme labels → save reviews_classified.json
```

**Why Groq?** ~500 tokens/sec, very low cost, ideal for classification.

**Folder:** `phase4_themes/`
**Files:** `theme_generator.py`

---

### Phase 5 — Weekly Pulse Generation (Gemini 2.5 Flash)

```
Input:  data/reviews_classified.json
Output: data/weekly_pulse.json
LLM:    Google Gemini 2.5 Flash

Flow:
  Aggregate stats per theme (count, avg rating)
        │
        ▼
  Rank themes by review count → top 4 (including 1 positive focus)
        │
        ▼
  Single Gemini 2.5 Flash call:
  ┌──────────────────────────────────────────┐
  │  System: You are a senior product        │
  │  analyst at a fintech company.           │
  │                                          │
  │  Prompt: Given classified reviews:       │
  │  1. Explain top 4 themes for leadership  │
  │  2. Pick 4 anonymised, impactful quotes  │
  │  3. Suggest 3 product improvements       │
  │                                          │
  │  Output: Structured JSON pulse object    │
  └──────────────────────────────────────────┘
        │
        ▼
  Validate schema → save weekly_pulse.json
```

**Why Gemini 2.5 Flash?** Best-in-class structured summarisation, strong reasoning, leadership-grade language quality, fast and cost-efficient.

**Folder:** `phase5_pulse/`
**Files:** `pulse_generator.py`

---

### Phase 6 — Email Draft & Delivery (Gemini 2.5 Flash)

```
Input:  data/weekly_pulse.json + templates/email_template.html
Output: data/email_draft.html + email sent
LLM:    Gemini 2.5 Flash (prose polishing)

Flow:
  Load pulse JSON
        │
        ▼
  Gemini 2.5 Flash: polish into professional prose (1 call)
        │
        ▼
  Render HTML via Jinja2 template
        │
        ▼
  Save → data/email_draft.html
        │
        ▼
  SMTP_SSL("smtp.gmail.com", 465)
  Authenticate → Send → Done
```

**Email UI One-Pager Design:**

```
┌─────────────────────────────────────────────────────┐
│  ┌───────────────────────────────────────────────┐  │
│  │  GRADIENT HEADER (Purple→Pink)               │  │
│  │  📊 Weekly Pulse · INDMoney User Sentiment    │  │
│  │  [ 📅 Mar 13–18, 2026 ]                       │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  ┌─────────┬─────────┬─────────┐  ← Stats Bar      │
│  │   187   │  ★ 3.4  │    5    │                    │
│  │ Reviews │ Avg Rtg │ Themes  │                    │
│  └─────────┴─────────┴─────────┘                    │
│                                                     │
│  Hi Team, Here's your weekly pulse...               │
│                                                     │
│  ── 🏷️ TOP THEMES ──────────────────────────────    │
│  ┌ Theme Card 1 (gradient bg, left border accent) ┐ │
│  │ 1. App Performance  [47 reviews · ★2.3]        │ │
│  │ Users report frequent crashes during...         │ │
│  └────────────────────────────────────────────────┘ │
│  ┌ Theme Card 2 ┐  ┌ Theme Card 3 ┐                │
│                                                     │
│  ── 💬 WHAT USERS ARE SAYING ────────────────────   │
│  ┌ Quote Card (frosted glass bg) ┐                  │
│  │ ❝ "The app freezes every time..." ★2            │ │
│  │   [App Performance]                              │ │
│  └───────────────────────────────┘                  │
│                                                     │
│  ── 🚀 SUGGESTED ACTIONS ────────────────────────   │
│  ┌ ● Action 1 — Optimise cold-start latency     ┐  │
│  ┌ ● Action 2 — Add fund comparison feature     ┐  │
│  ┌ ● Action 3 — Implement SLA-based escalation  ┐  │
│                                                     │
│  ── 📊 RATING DISTRIBUTION ──────────────────────   │
│  ★5  ████████░░░░░░  32%                            │
│  ★4  ██████░░░░░░░░  24%                            │
│  ★3  ████░░░░░░░░░░  16%                            │
│  ★2  ██████████░░░░  12%                            │
│  ★1  ████████░░░░░░  16%                            │
│                                                     │
│  ── FOOTER ──────────────────────────────────────   │
│  Best regards, Weekly Pulse Bot 🤖                   │
│  Auto-generated · PII removed · Groq + Gemini       │
└─────────────────────────────────────────────────────┘
```

**Template:** Self-contained HTML with all inline styles (no external CSS/JS).
Uses dark theme (#0f0f23 bg), gradient accents, and is compatible with
Gmail, Outlook, and Apple Mail.

**Applicable Rules:** P6.1–P6.6 (see [`rules.md`](../rules.md))

**Folder:** `phase6_email/`
**Files:** `email_sender.py`, `templates/email_template.html`

---

### Phase 7 — Streamlit Dashboard

```
Input:  data/weekly_pulse.json + data/reviews_classified.json
Output: Interactive web dashboard at http://localhost:8501

Streamlit reads JSON files directly — no separate backend needed.

Dashboard Sections:
  ┌────────────────────────────────────────────────┐
  │  st.metric() — 4 stat cards                   │
  │  (reviews, avg rating, themes, email status)   │
  ├────────────────────────────────────────────────┤
  │  st.expander() — Top 3 theme cards             │
  │  (theme name, count, avg rating, explanation)  │
  ├────────────────────────────────────────────────┤
  │  plotly.bar() — Rating distribution chart      │
  ├────────────────────────────────────────────────┤
  │  st.info() — User quote blocks with ratings    │
  ├────────────────────────────────────────────────┤
  │  st.success() — Action idea cards              │
  ├────────────────────────────────────────────────┤
  │  st.dataframe() — Review explorer (sidebar)    │
  └────────────────────────────────────────────────┘

Deployment:
  - Local:          streamlit run phase7_dashboard/app.py
  - Streamlit Cloud: share.streamlit.io (free hosting)

Theme:
  -similar to phase 6
  -light themed, keep a goog amount of spcing and padding
  -
```

**Why Streamlit over FastAPI + React?**

| Aspect | FastAPI + React | Streamlit |
|--------|----------------|-----------|
| Files to maintain | ~15+ across 2 folders | **1 Python file** |
| Separate backend | Yes | **No** (reads JSON directly) |
| Build step | npm run build | **None** |
| Deployment | Docker + hosting | **Streamlit Cloud (free)** |
| Language | Python + JS | **Python only** |

**Folder:** `phase7_dashboard/`
**Files:** `app.py`

---

### Phase 8 — Docker Containerisation

```
┌──────────────────────────────────────────────┐
│           Docker Container                   │
│                                              │
│  FROM python:3.11-slim                       │
│  WORKDIR /app                                │
│                                              │
│  COPY requirements.txt → pip install         │
│  COPY . .                                    │
│                                              │
│  ENV:                                        │
│    GROQ_API_KEY                              │
│    GEMINI_API_KEY                            │
│    EMAIL_ADDRESS                             │
│    EMAIL_APP_PASSWORD                        │
│    PORT=8501                                 │
│                                              │
│  Modes:                                      │
│   CMD ["python", "main.py"]         # Pipeline│
│   CMD ["streamlit", "run", "..."]   # Dashboard│
└──────────────────────────────────────────────┘
```

**Folder:** `phase8_docker/` (docs only — Dockerfile at repo root)
**Files:** `Dockerfile`, `.dockerignore` (at repo root)

---

### Phase 9 — GitHub Actions Scheduler

```
.github/workflows/weekly_pulse.yml

Trigger:
  ├── cron: "30 3 * * 1"  (Every Monday 9 AM IST / 3:30 AM UTC)
  └── workflow_dispatch   (Manual trigger button)

Steps:
  1. Checkout repo
  2. Setup Python 3.11
  3. Install dependencies
  4. Run: python main.py
  5. Upload data/ artifacts (retained 30 days)

Secrets:
  GROQ_API_KEY, GEMINI_API_KEY,
  EMAIL_ADDRESS, EMAIL_APP_PASSWORD
```

**Folder:** `phase9_scheduler/` (docs only)
**Files:** `.github/workflows/weekly_pulse.yml`

---

### Phase 10A — Fee Explanation: Mutual Fund Exit Load

```
Input:  INDMoney mutual fund page (e.g. HDFC Pharma & Healthcare Fund)
Output: data/fee_explanation.json

Flow:
  1. Scrape the INDMoney mutual fund page for exit load details
     URL pattern: https://www.indmoney.com/mutual-funds/<fund-slug>
         │
         ▼
  2. Parse exit load rules from the fund details section
         │
         ▼
  3. Structure into JSON with explanation bullets
         │
         ▼
  4. Save → data/fee_explanation.json

Output Schema:
  {
    "fee_scenario": "Mutual Fund Exit Load",
    "fund_name": "HDFC Pharma and Healthcare Fund Direct Growth",
    "explanation_bullets": [
      "Exit load of 1% if redeemed within 1 year from allotment",
      "No exit load after 1 year of holding",
      "Exit load is charged on the NAV at the time of redemption"
    ],
    "source_links": [
      "https://www.indmoney.com/mutual-funds/hdfc-pharma-and-healthcare-fund-direct-growth-1044289"
    ],
    "last_checked": "2026-03-25"
  }
```

**Integration with Phase 6 Email:**

The email template gains a new section after "Suggested Actions":

```
── 💰 FEE EXPLANATION ────────────────────────────

📋 Mutual Fund Exit Load
   Fund: HDFC Pharma and Healthcare Fund Direct Growth

   • Exit load of 1% if redeemed within 1 year from allotment
   • No exit load after 1 year of holding
   • Exit load is charged on the NAV at the time of redemption

   🔗 Source: indmoney.com/mutual-funds/...
```

**Why scrape INDMoney?** The app's own help pages provide the most accurate,
up-to-date exit load information. Users frequently ask about fees in reviews,
and proactively including this context helps leadership anticipate support queries.

**Folder:** `phase10_fee_explainer/`
**Files:** `fee_scraper.py`, `__init__.py`, `README.md`

---

### Phase 10B — Combined JSON to Google Docs (MCP)

```
Input:  data/weekly_pulse.json + data/fee_explanation.json
Output: Combined JSON appended to Google Doc via MCP

Flow:
  1. Load weekly_pulse.json and fee_explanation.json
         │
         ▼
  2. Merge into a single combined_pulse.json:
     ┌──────────────────────────────────────────┐
     │  {                                       │
     │    "date": "2026-03-15",                 │
     │    "weekly_pulse": {                     │
     │      "themes": [...],                    │
     │      "quotes": [...],                    │
     │      "action_ideas": [...]               │
     │    },                                    │
     │    "fee_scenario": "Mutual Fund Exit...",│
     │    "explanation_bullets": [...],          │
     │    "source_links": [...],                │
     │    "last_checked": "2026-03-15"          │
     │  }                                       │
     └──────────────────────────────────────────┘
         │
         ▼
  3. Save locally → data/combined_pulse.json
         │
         ▼
  4. Append to Google Doc via MCP:
     ┌──────────────────────────────────────────┐
     │  MCP Server: Google Docs                 │
     │  Action: Append content to document      │
     │  Document: Weekly Pulse Archive           │
     │  Content: JSON block for this week       │
     └──────────────────────────────────────────┘
```

**Combined JSON Schema:**

```json
{
  "date": "2026-03-15",
  "weekly_pulse": {
    "themes": ["Theme 1", "Theme 2", "Theme 3"],
    "quotes": ["Quote 1", "Quote 2", "Quote 3"],
    "action_ideas": ["Action 1", "Action 2", "Action 3"]
  },
  "fee_scenario": "Mutual Fund Exit Load",
  "explanation_bullets": [
    "Fact 1...",
    "Fact 2...",
    "Fact 3..."
  ],
  "source_links": ["Link 1", "Link 2"],
  "last_checked": "2026-03-15"
}
```

**Why MCP (Model Context Protocol)?**

| Aspect | Direct Google Docs API | MCP |
|--------|----------------------|-----|
| Auth complexity | OAuth2 service account setup | **MCP server handles auth** |
| Code to maintain | ~50 lines of API client code | **~10 lines MCP tool call** |
| Reusability | Custom per-project | **Standardised across AI agents** |
| Extensibility | Manual per-service | **Plug-and-play MCP servers** |

MCP provides a standardised interface for AI agents to interact with external
tools and services. Instead of hardcoding API SDK calls, our Python pipeline
acts as an **MCP Client**. It dynamically executes the external Google Docs
**MCP Server** via `stdio` (configured securely in `.env`). The Server handles
auth and documents, and our Client simply asks it to `append_document`.

 

**Google Doc Structure (Append-Only Archive):**

```
┌──────────────────────────────────────────────────────┐
│  📊 INDMoney Weekly Pulse Archive                     │
│                                                       │
│  ═══ Week of Mar 15, 2026 ═══════════════════════     │
│  { combined JSON block }                              │
│                                                       │
│  ═══ Week of Mar 08, 2026 ═══════════════════════     │
│  { combined JSON block }                              │
│                                                       │
│  ═══ Week of Mar 01, 2026 ═══════════════════════     │
│  { combined JSON block }                              │
│  ...                                                  │
└──────────────────────────────────────────────────────┘
```

**Folder:** `phase10_gdocs_mcp/`
**Files:** `gdocs_appender.py`, `json_combiner.py`, `__init__.py`, `README.md`

---

## 5. LLM Interaction Design

```mermaid
flowchart LR
    subgraph "Groq API — Fast + Cheap"
        A["Theme Discovery\n(1 call)"] --> B["Batch Classification\n(1-2 calls)"]
    end

    subgraph "Gemini 2.5 Flash — Quality + Structure"
        C["Pulse Summary\n(1 call)"] --> D["Email Polish\n(1 call)"]
    end

    B --> C

    style A fill:#F97316,color:#fff
    style B fill:#F97316,color:#fff
    style C fill:#8B5CF6,color:#fff
    style D fill:#8B5CF6,color:#fff
```

| # | Phase | Provider | Model | Calls | Purpose |
|---|-------|----------|-------|-------|---------|
| 1 | Phase 4 | **Groq** | `llama-3.3-70b-versatile` | 1 | Generate 3–5 themes |
| 2 | Phase 4 | **Groq** | `llama-3.3-70b-versatile` | 1–2 | Batch classify reviews |
| 3 | Phase 5 | **Gemini** | `gemini-2.5-flash` | 1 | Generate pulse JSON |
| 4 | Phase 6 | **Gemini** | `gemini-2.5-flash` | 1 | Polish email prose |

**Total LLM calls per run: 4–5 · ~30K tokens**

> **Note:** Phase 10A (Fee Explainer) and Phase 10B (Google Docs MCP) do **not** use LLM calls.
> Phase 10A uses web scraping (requests + BeautifulSoup). Phase 10B uses MCP tool calls.

### Token Budget Estimate

| Call | Input Tokens | Output Tokens | Cost (est.) |
|------|------------:|-------------:|------------:|
| Theme discovery | ~8,000 | ~200 | ~$0.002 |
| Batch classification | ~10,000 | ~2,000 | ~$0.003 |
| Pulse generation | ~6,000 | ~1,500 | ~$0.001 |
| Email polish | ~2,000 | ~1,000 | ~$0.001 |
| **Total** | **~26,000** | **~4,700** | **~$0.007** |

---

## 6. Repository Structure

```
WeeklyPulse_PlaystoreReviews/
│
├── main.py                              # Pipeline orchestrator
│
├── phase1_setup/                        # Phase 1: Config & Clients
│   ├── README.md
│   ├── __init__.py
│   ├── config.py                        # Env vars & constants
│   ├── llm_clients.py                   # Groq + Gemini 2.5 Flash wrappers
│   └── logger.py                        # Structured logging
│
├── phase2_scraper/                      # Phase 2: Review Ingestion
│   ├── README.md
│   ├── __init__.py
│   └── scraper.py                       # Play Store scraping
│
├── phase3_cleaning/                     # Phase 3: Data Cleaning
│   ├── README.md
│   ├── __init__.py
│   └── cleaner.py                       # PII removal & normalisation
│
├── phase4_themes/                       # Phase 4: Theme Generation
│   ├── README.md
│   ├── __init__.py
│   └── theme_generator.py              # Groq LLaMA 3.3 theming
│
├── phase5_pulse/                        # Phase 5: Pulse Generation
│   ├── README.md
│   ├── __init__.py
│   └── pulse_generator.py              # Gemini 2.5 Flash summaries
│
├── phase6_email/                        # Phase 6: Email Delivery
│   ├── README.md
│   ├── __init__.py
│   ├── email_sender.py                  # Draft + SMTP delivery
│   └── templates/
│       └── email_template.html          # Jinja2 HTML template
│
├── phase7_dashboard/                    # Phase 7: Streamlit Dashboard
│   ├── README.md
│   ├── __init__.py
│   └── app.py                           # Streamlit application
│
├── phase8_docker/                       # Phase 8: Containerisation (docs)
│   └── README.md
│
├── phase9_scheduler/                    # Phase 9: GitHub Actions (docs)
│   └── README.md
│
├── phase10_fee_explainer/               # Phase 10A: Fee Explanation
│   ├── README.md
│   ├── __init__.py
│   └── fee_scraper.py                   # Scrape MF exit load from INDMoney
│
├── phase10_gdocs_mcp/                   # Phase 10B: Google Docs MCP
│   ├── README.md
│   ├── __init__.py
│   ├── json_combiner.py                 # Merge pulse + fee into combined JSON
│   └── gdocs_appender.py               # Append combined JSON to Google Docs via MCP
│
├── .streamlit/
│   └── config.toml                      # Streamlit theme config
│
├── .github/
│   └── workflows/
│       └── weekly_pulse.yml             # Cron workflow
│
├── architecture/
│   └── architecture.md                  # This document
│
├── rules.md                                 # 📏 Rules & guardrails (50+ rules, per-phase)
│
├── tests/
│   ├── test_phase1.py                   # Phase 1 test suite
│   ├── test_phase10a.py                 # Phase 10A test suite
│   └── test_phase10b.py                 # Phase 10B test suite
│
├── data/                                # Runtime outputs (gitignored)
│   ├── reviews_raw.json
│   ├── reviews_cleaned.json
│   ├── reviews_classified.json
│   ├── weekly_pulse.json
│   ├── fee_explanation.json
│   ├── combined_pulse.json
│   └── email_draft.html
│
├── Dockerfile
├── .dockerignore
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 7. Dashboard Architecture (Phase 7 — Streamlit)

```mermaid
flowchart TD
    A["app.py"] --> B["Load data/*.json"]
    B --> C["st.metric x4"]
    B --> D["st.expander x3\n(Theme Cards)"]
    B --> E["plotly.bar\n(Rating Chart)"]
    B --> F["st.info x3\n(User Quotes)"]
    B --> G["st.success x3\n(Action Ideas)"]
    B --> H["st.dataframe\n(Review Explorer)"]
    B --> I["st.sidebar\n(Filters)"]

    style A fill:#FF4B4B,color:#fff
    style E fill:#8B5CF6,color:#fff
```

### Key Advantages of Streamlit

```
                        Streamlit
                     ┌─────────────┐
                     │             │
  data/*.json  ────▶ │  app.py     │ ────▶  Browser
                     │  (1 file)   │        :8501
                     │             │
                     └─────────────┘
         No backend server needed!
         No build step!
         Deploy free on Streamlit Cloud!
```

---

## 8. Security & Privacy

| Concern | Mitigation |
|---------|------------|
| PII in reviews | Phase 3 strips emails, phone numbers, ID patterns |
| API keys | Environment variables only — never committed |
| Email credentials | Gmail App Password, not main password |
| LLM data exposure | All PII removed before any LLM call (Phase 3) |
| Docker secrets | `.env` in `.dockerignore` + `.gitignore` |
| GitHub secrets | Stored in repo Settings → Secrets → Actions |
| Streamlit secrets | Stored in Streamlit Cloud secrets manager |

---

## 9. Error Handling Strategy

| Phase | Failure Mode | Recovery |
|-------|-------------|----------|
| Phase 2 | Play Store rate-limit | Retry with exponential backoff (max 3) |
| Phase 3 | Regex edge case | Log warning; preserve original text |
| Phase 4 | Groq API timeout | Retry once; fallback to smaller batch |
| Phase 5 | Gemini 2.5 Flash error | Retry once; save partial output |
| Phase 6 | SMTP auth failure | Save draft locally; log error |
| Phase 7 | JSON files not found | Streamlit shows "Run pipeline first" warning |
| Phase 9 | GitHub Actions failure | GitHub email notification; manual re-trigger |
| Phase 10A | INDMoney page 403/timeout | Use cached `fee_explanation.json`; log warning. Email renders without fee section if no data. |
| Phase 10B | MCP server unavailable | Save `combined_pulse.json` locally; skip Google Docs append. Log error. |
| Phase 10B | Google Docs auth failure | Log error; pipeline continues (append is non-critical). |

---

## 10. Execution Modes

### Mode 1 — Pipeline Only (Headless)

```bash
python main.py
# Runs: Phase 1 → 2 → 3 → 4 → 5 → 10A → 6 → 10B (email sent + Google Doc updated)
```

### Mode 2 — Dashboard (Streamlit)

```bash
streamlit run phase7_dashboard/app.py
# Opens: http://localhost:8501
```

### Mode 3 — Full Platform (Docker)

```bash
docker run --env-file .env -p 8501:8501 weekly-pulse \
  sh -c "python main.py && streamlit run phase7_dashboard/app.py --server.port 8501 --server.address 0.0.0.0"
```

### Mode 4 — Streamlit Cloud

```
1. Push to GitHub
2. Connect at share.streamlit.io
3. Set secrets
4. Deploy (free!)
```

---

## 11. Execution Timeline

```mermaid
gantt
    title Pipeline Execution Timeline
    dateFormat X
    axisFormat %s

    section Data Collection
    Phase 2 - Scrape Reviews    :0, 30
    Phase 3 - Clean & Strip PII :30, 40

    section AI Processing
    Phase 4 - Theme Generation  :40, 60
    Phase 5 - Pulse Generation  :60, 75

    section Delivery
    Phase 6 - Email & Send      :75, 90

    section Dashboard
    Phase 7 - Streamlit Start   :90, 95
```

**Typical execution time: ~95 seconds for pipeline (incl. fee scrape + MCP append) + instant Streamlit start**

---

## 12. New Feature Details

### 12.1 Fee Explanation — Mutual Fund Exit Load (Phase 10A)

```mermaid
flowchart LR
    A["INDMoney\nMutual Fund Page"] -->|"requests +\nBeautifulSoup"| B["Phase 10A:\nFee Scraper"]
    B -->|"fee_explanation.json"| C["Phase 6: Email"]
    B -->|"fee_explanation.json"| D["Phase 10B:\nJSON Combiner"]

    style A fill:#4285F4,color:#fff
    style B fill:#F59E0B,color:#fff
    style C fill:#10B981,color:#fff
    style D fill:#8B5CF6,color:#fff
```

**Purpose:** Users frequently ask about mutual fund fees in Play Store reviews.
By proactively scraping exit load details from INDMoney's own fund pages,
the weekly pulse email can include a "Fee Explanation" section that helps
leadership anticipate and address fee-related support queries.

**Email Integration:**

```
┌─────────────────────────────────────────────────────┐
│  ... (existing email sections) ...                  │
│                                                     │
│  ── 💰 FEE EXPLANATION ─────────────────────────    │
│  ┌ Fee Card (amber accent, left border) ──────────┐ │
│  │ 📋 Mutual Fund Exit Load                       │ │
│  │ Fund: HDFC Pharma and Healthcare Fund          │ │
│  │                                                 │ │
│  │ • Exit load of 1% if redeemed within 1 year    │ │
│  │ • No exit load after 1 year of holding         │ │
│  │ • Charged on NAV at time of redemption         │ │
│  │                                                 │ │
│  │ 🔗 Source: indmoney.com/mutual-funds/...        │ │
│  └─────────────────────────────────────────────────┘ │
│                                                     │
│  ... (footer) ...                                   │
└─────────────────────────────────────────────────────┘
```

**Configurable Fund URL:** The target fund URL is stored in `config.py`
as `FEE_FUND_URL`, making it easy to change the fund being tracked
without modifying scraper logic.

---

### 12.2 Combined JSON to Google Docs via MCP (Phase 10B)

```mermaid
flowchart TD
    A["weekly_pulse.json"] --> C["JSON Combiner"]
    B["fee_explanation.json"] --> C
    C -->|"combined_pulse.json"| D["MCP: Google Docs"]
    D -->|"Append"| E["Google Doc:\nWeekly Pulse Archive"]

    style C fill:#8B5CF6,color:#fff
    style D fill:#4285F4,color:#fff
    style E fill:#34A853,color:#fff
```

**Purpose:** Create a persistent, shareable archive of all weekly pulse reports
in a Google Doc. Leadership and stakeholders can access the full history
without needing pipeline access or the Streamlit dashboard.

**MCP Flow:**

```
┌────────────────────┐     ┌──────────────────────────────────────────────────┐
│  Pipeline (Python) │────▶│  MCP Client (mcp SDK)                            │
│                    │     │  Reads MCP_GOOGLE_DOCS_SERVER_CMD from .env      │
└────────────────────┘     └──────────────────────────────────────────────────┘
                                               │
                                               ▼ (STDIO / Exec)
                           ┌──────────────────────────────────────────────────┐
                           │  MCP Server (Google Docs)                        │
                           │  e.g., node / npx @anthropic/mcp-google-docs     │
                           │  Uses GOOGLE_DOCS_CREDENTIALS for auth           │
                           └──────────────────────────────────────────────────┘
                                               │
                                               ▼
                                    ┌──────────────────┐
                                    │  Google Docs API │
                                    │  (append content)│
                                    └──────────────────┘
```

**Environment Variables (Phase 10B):**

| Variable | Purpose | Default / Example |
|----------|---------|-------------------|
| `GOOGLE_DOC_ID` | Target Google Doc ID for archiving | `1A2B3c4D5e...` |
| `GOOGLE_DOCS_CREDENTIALS` | Path to Google service account JSON | `path/to/credentials.json` |
| `MCP_GOOGLE_DOCS_SERVER_CMD` | Executable to start the MCP Server | `npx` |
| `MCP_GOOGLE_DOCS_SERVER_ARGS` | Arguments for the MCP Server proxy | `-y @anthropic/mcp-google-docs` |

| Variable | Purpose | Where to Get |
|----------|---------|--------------|
| `GOOGLE_DOCS_CREDENTIALS` | Path to Google service account JSON | [Google Cloud Console](https://console.cloud.google.com) |
| `GOOGLE_DOC_ID` | Target Google Doc ID for archiving | Create a Google Doc, copy ID from URL |
| `FEE_FUND_URL` | INDMoney mutual fund page URL to scrape | [indmoney.com/mutual-funds](https://www.indmoney.com/mutual-funds) |

**Applicable Rules:** All global rules (G1–G8) apply. New feature-specific rules
should be added to `rules.md` under Phase 10A and Phase 10B sections.
