<div align="center">

# 🐳 Phase 8 — Docker Containerisation

**Package the entire platform (pipeline + Streamlit dashboard) into a portable Docker container**

[![Phase](https://img.shields.io/badge/Phase-8%20of%209-blue)]()
[![Docker](https://img.shields.io/badge/Docker-Containerised-2496ED?logo=docker&logoColor=white)]()
[![Base](https://img.shields.io/badge/Base-python%3A3.11--slim-3776AB?logo=python&logoColor=white)]()
[![Status](https://img.shields.io/badge/Status-Architecture-yellow)]()

</div>

---

## 🧠 Problem → Solution → Impact

| | |
|---|---|
| **❌ Problem** | "Works on my machine" — Python version mismatches, missing packages, OS-specific issues make deployment painful |
| **✅ Solution** | A single Dockerfile builds a self-contained image with all dependencies, pipeline code, and Streamlit dashboard |
| **📈 Impact** | Run anywhere (laptop, server, CI/CD, cloud) with one command: `docker run --env-file .env weekly-pulse` |

---

## 📋 What This Phase Does

```mermaid
flowchart TD
    A["Dockerfile"] --> B["python:3.11-slim base"]
    B --> C["pip install requirements"]
    C --> D["COPY application code"]
    D --> E["Container Ready"]

    subgraph "Runtime Modes"
        F["Pipeline Mode\npython main.py"] --> G["📧 Email Sent"]
        H["Dashboard Mode\nstreamlit run app.py"] --> I["🌐 Dashboard Live"]
    end

    E --> F
    E --> H

    style A fill:#2496ED,color:#fff
    style G fill:#10B981,color:#fff
    style I fill:#EC4899,color:#fff
```

---

## 📁 Files

```
phase8_docker/
└── README.md               # This file (instructions only)

# The actual Docker files live at the repo root:
├── Dockerfile               # Container definition
├── .dockerignore            # Build exclusions
└── .env.example             # Env var template
```

> The Dockerfile stays at the repo root per Docker convention. This folder contains documentation only.

---

## 🐳 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Layer-cached dependency install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create output directory
RUN mkdir -p /app/data

ENV PORT=8501
EXPOSE ${PORT}

# Default: run pipeline then start dashboard
CMD ["python", "main.py"]
```

---

## 📦 .dockerignore

```
.env
.git/
data/
*.md
architecture/
__pycache__/
*.pyc
venv/
.venv/
.vscode/
.idea/
phase8_docker/
phase9_scheduler/
```

---

## ▶️ How to Run

### Build the Image

```bash
docker build -t weekly-pulse .
```

### Run — Pipeline Mode (scrape → email)

```bash
docker run --env-file .env weekly-pulse
```

### Run — Dashboard Mode (Streamlit)

```bash
docker run --env-file .env -p 8501:8501 weekly-pulse \
  streamlit run phase7_dashboard/app.py --server.port 8501 --server.address 0.0.0.0
```

### Run — Full Platform (pipeline + dashboard)

```bash
docker run --env-file .env -p 8501:8501 weekly-pulse \
  sh -c "python main.py && streamlit run phase7_dashboard/app.py --server.port 8501 --server.address 0.0.0.0"
```

### Mount Data Locally

```bash
docker run --env-file .env -v $(pwd)/data:/app/data weekly-pulse
```

---

## 🏗️ Image Size Optimization

| Strategy | Impact |
|----------|--------|
| `python:3.11-slim` base | ~120MB vs ~900MB for full Python |
| `--no-cache-dir` for pip | Saves ~50MB in pip caches |
| `.dockerignore` excludes docs, git, data | Minimal build context |
| No dev dependencies | Only production packages |

**Expected image size: ~250MB**

---

## ⚠️ Error Handling

| Scenario | Strategy |
|----------|----------|
| Build failure | Check `requirements.txt` syntax and network |
| Missing env vars | Pipeline fails fast with clear error on startup |
| Port conflict | Use `-p <other>:8501` to remap |
| Permission errors | Ensure `data/` is writable in container |

---

## ✅ Success Criteria

- [ ] `docker build` completes without errors
- [ ] Pipeline mode runs and sends email
- [ ] Dashboard mode serves Streamlit at port 8501
- [ ] Image size < 300MB
- [ ] No secrets baked into the image (verified with `docker history`)
