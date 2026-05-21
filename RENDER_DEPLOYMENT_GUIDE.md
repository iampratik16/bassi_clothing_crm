# 🚀 Bassi Clothing AI Marketing CRM — Render Deployment Guide

> **Share this guide** with anyone who has a copy of this project and wants to host it on [Render](https://render.com) for free.
> This guide was written for use with **Antigravity** (AI coding assistant) — paste this entire file into Antigravity and ask it to help execute each step.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Push Your Code to GitHub](#2-push-your-code-to-github)
3. [Create a Render Account](#3-create-a-render-account)
4. [Deploy on Render — Step by Step](#4-deploy-on-render--step-by-step)
5. [Set Environment Variables on Render](#5-set-environment-variables-on-render)
6. [Understanding the Key Deployment Files](#6-understanding-the-key-deployment-files)
7. [The Keep-Alive Ping (Prevents Free-Tier Sleep)](#7-the-keep-alive-ping-prevents-free-tier-sleep)
8. [Post-Deployment Verification](#8-post-deployment-verification)
9. [Updating Your Deployed App](#9-updating-your-deployed-app)
10. [Troubleshooting](#10-troubleshooting)
11. [Using Antigravity to Help](#11-using-antigravity-to-help)

---

## 1. Prerequisites

Before you begin, make sure you have:

- [ ] **Git** installed on your machine (`git --version` to check)
- [ ] A **GitHub account** (free) → [github.com](https://github.com)
- [ ] A **Render account** (free) → [render.com](https://render.com)
- [ ] **Python 3.11** installed locally (for testing, optional)
- [ ] The project source code on your laptop
- [ ] Your own API keys and SMTP credentials (see [Section 5](#5-set-environment-variables-on-render) for the full list)

---

## 2. Push Your Code to GitHub

Render deploys from a GitHub repository. You need your project in a GitHub repo first.

### 2.1 — Initialize Git (if not already done)

Open a terminal in your project root folder and run:

```bash
cd /path/to/your/AI_Marketing

# Initialize git (skip if .git folder already exists)
git init
git branch -M main
```

### 2.2 — Verify `.gitignore`

Make sure your `.gitignore` contains at least these entries so you don't push secrets or junk:

```gitignore
# Bassi Clothing — AI Marketing Skills Toolkit
.env
__pycache__/
*.pyc
*.pyo
.DS_Store
data/leads.json
output/
*.db
.venv/
venv/
node_modules/
```

> [!CAUTION]
> **NEVER push your `.env` file to GitHub.** It contains your Gemini API key and SMTP password. The `.gitignore` above already excludes it.

### 2.3 — Create a GitHub Repository

1. Go to [github.com/new](https://github.com/new)
2. Name it `bassi_clothing_crm`
3. Set it to **Private** (recommended since it has business logic and lead data)
4. Do **NOT** initialize with README (you already have code)
5. Click **Create repository**

### 2.4 — Push Your Code

```bash
# Add the remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/bassi_clothing_crm.git

# Stage, commit, and push
git add .
git commit -m "Initial commit: Bassi Clothing AI Marketing CRM"
git push -u origin main
```

> [!TIP]
> If `git remote add origin` gives an error saying remote already exists, use:
> ```bash
> git remote set-url origin https://github.com/YOUR_USERNAME/bassi_clothing_crm.git
> ```

---

## 3. Create a Render Account

1. Go to [render.com](https://render.com) and click **Get Started for Free**
2. **Sign up with your GitHub account** — this is the easiest way as it auto-links your repos
3. Authorize Render to access your GitHub repositories when prompted

---

## 4. Deploy on Render — Step by Step

### 4.1 — Create a New Web Service

1. Log into [dashboard.render.com](https://dashboard.render.com)
2. Click the **"New +"** button (top right)
3. Select **"Web Service"**

### 4.2 — Connect Your Repository

1. Choose **"Build and deploy from a Git repository"** → click **Next**
2. Find your `bassi_clothing_crm` repo in the list
   - If you don't see it, click **"Configure account"** to grant Render access to the repo
3. Click **"Connect"** next to your repo

### 4.3 — Configure the Service

Fill in the following settings:

| Setting | Value |
|---------|-------|
| **Name** | `bassi-crm` (or any name you like — this becomes your subdomain) |
| **Region** | Pick the closest to your users (e.g., `Frankfurt (EU Central)` for UK/Europe) |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn dashboard.app:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | **Free** |

> [!IMPORTANT]
> The **Start Command** is critical. It must be exactly:
> ```
> uvicorn dashboard.app:app --host 0.0.0.0 --port $PORT
> ```
> - `dashboard.app:app` → tells uvicorn to find the `app` object inside `dashboard/app.py`
> - `--host 0.0.0.0` → makes it accessible externally (not just localhost)
> - `--port $PORT` → Render injects the `PORT` environment variable; you **must** use it

### 4.4 — Click "Create Web Service"

Render will now:
1. Clone your repo
2. Run `pip install -r requirements.txt`
3. Start the app with the start command

The first deploy takes **3–5 minutes**. You can watch the build logs in real time.

### 4.5 — Get Your Live URL

Once deployed, Render gives you a URL like:
```
https://bassi-crm.onrender.com
```

This is your live dashboard! 🎉

---

## 5. Set Environment Variables on Render

Your app needs API keys and config that live in `.env` locally. On Render, these are set via the dashboard.

### 5.1 — Navigate to Environment Variables

1. Go to your service on [dashboard.render.com](https://dashboard.render.com)
2. Click the **"Environment"** tab on the left sidebar
3. Click **"Add Environment Variable"** for each one below

### 5.2 — Required Environment Variables

Add **each** of these key-value pairs (these match `render.yaml`):

| Key | Example Value | Description |
|-----|---------------|-------------|
| `PYTHON_VERSION` | `3.11.9` | Tells Render which Python to use |
| `GEMINI_API_KEY` | `your_gemini_api_key_here` | Google Gemini API key for AI email generation |
| `SMTP_HOST` | `smtpout.secureserver.net` | SMTP host (GoDaddy default; use your provider's host) |
| `SMTP_PORT` | `465` | SMTP port (`465` for SSL, `587` for STARTTLS) |
| `SMTP_USERNAME` | `pratik@bassiclothing.in` | SMTP login (your sending mailbox) |
| `SMTP_PASSWORD` | `your_smtp_password` | SMTP password / app password |
| `SENDER_EMAIL` | `pratik@bassiclothing.in` | The "From" email address |
| `SENDER_NAME` | `Bassi Clothing` | The "From" display name |
| `DASHBOARD_HOST` | `0.0.0.0` | Bind address (must be `0.0.0.0` on Render) |
| `DASHBOARD_PORT` | `10000` | Internal port — Render still injects its own `$PORT`, this is for local fallback |
| `MAX_EMAILS_PER_DAY` | `100` | Daily sending limit (start low for domain warmup) |
| `EMAIL_DELAY_SECONDS` | `5` | Seconds between each email send |
| `DRY_RUN` | `false` | Set to `true` for testing (emails logged, not sent). Set `false` to actually send |
| `SECRET_KEY` | *(auto-generated)* | Mark this as **Generate Value** in Render so it's a random secret |
| `APOLLO_API_KEY` | `your_apollo_key` | *(optional)* Apollo.io API key for lead search |
| `OPENAI_API_KEY` | `sk-...` | *(optional)* OpenAI key for content ops |
| `OPENAI_MODEL` | `gpt-4o-mini` | *(optional)* OpenAI model |

> [!TIP]
> **Start with `DRY_RUN=true`** to verify everything works before sending real emails. Check the logs to confirm emails are being "sent" in dry-run mode, then switch to `false`.

### 5.3 — ⚠️ SMTP and Render's Free Tier

> [!CAUTION]
> **Render's free tier blocks outbound SMTP ports (25, 465, 587).** This project sends email via SMTP (`smtpout.secureserver.net:465`), so SMTP sending **will likely fail silently on Render Free**.
>
> Your options:
> 1. **Upgrade to a paid Render plan** — paid instances allow outbound SMTP.
> 2. **Switch to an HTTPS email provider** like [Resend](https://resend.com) (port 443, not blocked) and update `outbound_engine/email_sender.py` to call its API. This is a code change, not just a config change.
> 3. **Run the dashboard elsewhere** (e.g., a small VPS like Hetzner/DigitalOcean) where SMTP is unrestricted.
>
> The rest of the app (lead management, AI generation, dashboard UI) will run fine on Render free — only the actual *send* step is affected.

---

## 6. Understanding the Key Deployment Files

This project uses **2 files** for Render deployment (your friend's project has 4 — this one is leaner and relies on `render.yaml` alone for runtime info):

### 6.1 — `render.yaml` (Blueprint Spec)

This file tells Render how to deploy your app automatically. It defines the service type, build/start commands, and all environment variables.

```yaml
services:
  - type: web
    name: bassi-crm
    runtime: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn dashboard.app:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: "3.11.9"
      - key: GEMINI_API_KEY
        sync: false        # ← "sync: false" means you set this manually in Render UI
      - key: SMTP_HOST
        sync: false
      # ... (other env vars)
      - key: SECRET_KEY
        generateValue: true
```

> **`sync: false`** = Render will NOT auto-set this; you must enter it manually in the Environment tab. This is used for secrets.
>
> **`generateValue: true`** = Render generates a random value for you (used for `SECRET_KEY`).

### 6.2 — `requirements.txt`

All Python dependencies. Render runs `pip install -r requirements.txt` during build:

```
google-genai>=1.0.0
httpx>=0.27.0
fastapi>=0.115.0
uvicorn[standard]>=0.34.0
python-multipart>=0.0.9
aiosmtplib>=3.0.0
jinja2>=3.1.0
pandas>=2.2.0
pyyaml>=6.0.0
python-dotenv>=1.0.0
aiofiles>=24.1.0
openpyxl>=3.1.0
requests>=2.31.0
rich>=13.7.0
click>=8.1.0
python-dateutil>=2.9.0
```

> [!NOTE]
> This project does **not** include a `Procfile` or `runtime.txt`. The Python version is set via the `PYTHON_VERSION` env var in `render.yaml`, and the start command is set via `startCommand` in the same file — so neither extra file is needed.

---

## 7. The Keep-Alive Ping (Prevents Free-Tier Sleep)

> [!IMPORTANT]
> **Render's free tier spins down your service after 15 minutes of inactivity.** When someone visits after a spin-down, it takes ~30–60 seconds to cold-start. A keep-alive ping prevents this.

### Current Status

> [!CAUTION]
> **This project does NOT currently include a keep-alive pinger.** Your friend's NeoEco project has one built in; yours doesn't yet. If you deploy to Render Free without adding it, the dashboard will sleep after 15 minutes of inactivity.
>
> The instructions below show what to add. This is a one-time code change.

### What to Add

Open `dashboard/app.py` and add the following near the top (after the existing imports):

```python
import httpx
from contextlib import asynccontextmanager

KEEP_ALIVE_URL = "https://YOUR-APP-NAME.onrender.com/api/health"
KEEP_ALIVE_INTERVAL = 14 * 60  # 14 minutes in seconds


async def _keep_alive_pinger():
    """Ping /api/health every 14 minutes to prevent Render free-tier spin-down."""
    async with httpx.AsyncClient(timeout=30) as client:
        while True:
            await asyncio.sleep(KEEP_ALIVE_INTERVAL)
            try:
                resp = await client.get(KEEP_ALIVE_URL)
                print(f"[keep-alive] pinged {KEEP_ALIVE_URL} → {resp.status_code}")
            except Exception as e:
                print(f"[keep-alive] ping failed: {e}")


@asynccontextmanager
async def lifespan(app):
    """Manage background tasks on startup/shutdown."""
    keep_alive_task = asyncio.create_task(_keep_alive_pinger())
    print("[startup] Keep-alive pinger started")
    yield
    keep_alive_task.cancel()
    print("[shutdown] Keep-alive pinger cancelled")
```

Then update the existing `app = FastAPI(...)` line to attach the lifespan:

```python
app = FastAPI(
    title="Bassi Clothing — AI Marketing Dashboard",
    description="B2B Outbound Engine, Sales Pipeline, and Content Ops",
    lifespan=lifespan,
)
```

The health endpoint **already exists** in `dashboard/app.py` (around line 1060):

```python
@app.get("/api/health")
async def health():
    return {"status": "healthy", ...}
```

### ⚡ What You MUST Change

> [!CAUTION]
> After deploying, you **MUST** update the `KEEP_ALIVE_URL` to match **your** Render URL:
> ```python
> KEEP_ALIVE_URL = "https://YOUR-APP-NAME.onrender.com/api/health"
> ```
> Replace `YOUR-APP-NAME` with your actual Render service name (e.g., `bassi-crm`). If you skip this, the ping will hit someone else's URL (or fail), and your app **will** sleep after 15 minutes.

After changing, commit and push:

```bash
git add dashboard/app.py
git commit -m "Add keep-alive pinger for Render free tier"
git push origin main
```

Render will auto-redeploy with the updated URL.

---

## 8. Post-Deployment Verification

After deployment, verify everything is working:

### 8.1 — Check the Dashboard Loads

Visit your Render URL in a browser:
```
https://YOUR-APP-NAME.onrender.com
```

You should see the Bassi Clothing AI Marketing Dashboard with tabs for Leads, Campaigns, Sent Mails, Pipeline, etc.

### 8.2 — Check the Health Endpoint

```
https://YOUR-APP-NAME.onrender.com/api/health
```

Should return JSON with `"status": "healthy"`.

### 8.3 — Check the Logs

1. Go to your service on [dashboard.render.com](https://dashboard.render.com)
2. Click the **"Logs"** tab
3. Look for:
   ```
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://0.0.0.0:10000
   ```
4. If you added the keep-alive pinger, after ~14 minutes you should also see:
   ```
   [keep-alive] pinged https://YOUR-APP-NAME.onrender.com/api/health → 200
   ```

### 8.4 — Test Email Generation (Dry Run)

1. Import some test leads via the Dashboard (Excel upload or Apollo search)
2. Try generating an email for a lead via the **Emails** tab
3. With `DRY_RUN=true`, click "Send" and check the logs — it should log the email without actually sending

---

## 9. Updating Your Deployed App

Render auto-deploys whenever you push to `main`. To update:

```bash
# Make your changes locally, then:
git add .
git commit -m "Your change description"
git push origin main
```

Render will automatically detect the push and redeploy (takes ~2–4 minutes).

> [!NOTE]
> **Ephemeral filesystem warning**: Render's free tier wipes the filesystem on every redeploy. This means:
> - `data/leads.json`, `data/replies.json`, `data/campaigns.json` — all reset on each redeploy
> - `output/send_logs/*.json` (local send logs) — lost
> - `output/generated_emails.json` — lost
>
> If you need persistence, either:
> - Re-import leads via Excel upload after each redeploy, or
> - Upgrade to a paid Render plan with a persistent disk attached, or
> - Move lead/campaign storage to a managed database (e.g., Render Postgres).

---

## 10. Troubleshooting

### ❌ Build fails: `ModuleNotFoundError`
- Make sure all dependencies are in `requirements.txt`
- Check the build logs for the specific missing module and add it

### ❌ App crashes on start: `Error loading ASGI app`
- Verify the start command: `uvicorn dashboard.app:app --host 0.0.0.0 --port $PORT`
- Make sure `dashboard/app.py` exists and has `app = FastAPI(...)`

### ❌ Emails not sending (no errors in logs)
- **Render blocks SMTP ports on the free tier.** See [Section 5.3](#53--smtp-and-renders-free-tier).
- Check `DRY_RUN` — if it's `true`, emails are logged but not sent.
- Check `SMTP_USERNAME` / `SMTP_PASSWORD` are set correctly in the Render Environment tab.
- For GoDaddy SMTP, make sure the mailbox isn't rate-limited or locked.

### ❌ App sleeps after 15 minutes
- This project doesn't ship with keep-alive — add the code from [Section 7](#7-the-keep-alive-ping-prevents-free-tier-sleep).
- After adding, check that `KEEP_ALIVE_URL` matches your actual Render URL.
- Look in logs for `[keep-alive] pinged ... → 200` messages every ~14 min.

### ❌ Gemini API errors (429 / quota exceeded)
- The free Gemini tier allows ~15 requests per minute.
- Reduce batch sizes when generating emails for many leads at once, or upgrade your Gemini API plan.

### ❌ Data lost after redeploy
- This is expected on Render's free tier (ephemeral disk).
- Re-import leads via Excel upload or Apollo search after redeploy.
- For permanent storage, attach a persistent disk (paid plan) or move to a managed DB.

### ❌ `Daily limit reached` in send logs
- This is the `MAX_EMAILS_PER_DAY` cap in `email_sender.py`. Raise it in the Render Environment tab and trigger a redeploy.

---

## 11. Using Antigravity to Help

You can use **Antigravity** (the AI coding assistant) to help with every step. Some prompts you can use:

### Setting Up the Repo
> *"Help me initialize this project as a git repo and push it to GitHub"*

### Deploying to Render
> *"I have this project ready on GitHub. Help me deploy it to Render as a free web service"*

### Adding the Keep-Alive Pinger
> *"Add a keep-alive pinger to dashboard/app.py that hits /api/health every 14 minutes, and point it to https://bassi-crm.onrender.com/api/health"*

### Adding Environment Variables
> *"Show me all the environment variables I need to set on Render for this project"*

### Debugging Deployment Issues
> *"My Render deployment is failing with this error: [paste error]. Help me fix it"*

### Switching from Dry Run to Live
> *"I've tested in dry-run mode and everything works. Help me switch DRY_RUN to false on Render and send my first batch"*

### Migrating SMTP to Resend
> *"Render is blocking my SMTP sends. Help me migrate outbound_engine/email_sender.py to use the Resend HTTPS API instead"*

---

## Quick Reference — Complete Deployment Checklist

```
1.  [ ] Git init + push to GitHub (private repo: bassi_clothing_crm)
2.  [ ] Create Render account (sign up with GitHub)
3.  [ ] New Web Service → connect your repo
4.  [ ] Set Runtime: Python 3, Branch: main
5.  [ ] Set Build Command: pip install -r requirements.txt
6.  [ ] Set Start Command: uvicorn dashboard.app:app --host 0.0.0.0 --port $PORT
7.  [ ] Select Free instance type
8.  [ ] Click "Create Web Service"
9.  [ ] Add ALL environment variables (Section 5)
10. [ ] Wait for first deploy to complete (~3-5 min)
11. [ ] Visit your URL → verify dashboard loads
12. [ ] Visit /api/health → verify {"status": "healthy"}
13. [ ] (Recommended) Add keep-alive pinger to dashboard/app.py → git push
14. [ ] Wait for auto-redeploy
15. [ ] Check logs for "[keep-alive] pinged ... → 200" after 14 min
16. [ ] Test email generation with DRY_RUN=true
17. [ ] Confirm SMTP works (if on paid plan) OR switch provider (see Section 5.3)
18. [ ] When ready, set DRY_RUN=false on Render
19. [ ] 🎉 You're live!
```

---

## Project Architecture (For Reference)

```
AI_Marketing/
├── dashboard/
│   ├── app.py                 ← Main FastAPI app
│   └── static/                ← Dashboard frontend (HTML/CSS/JS)
├── outbound_engine/
│   ├── apollo_search.py       ← Apollo.io lead search
│   ├── campaign_tracker.py    ← Campaign management
│   ├── email_generator.py     ← Gemini-powered email writing
│   ├── email_sender.py        ← Email sending (SMTP via smtplib/aiosmtplib)
│   ├── lead_manager.py        ← Lead CRM operations
│   └── reply_tracker.py       ← IMAP reply scanning
├── content_ops/               ← Content generation modules
├── sales_pipeline/            ← Lead scoring & deal tracking
├── data/                      ← Leads, campaigns, replies, opens (JSON)
├── output/                    ← Generated emails, send logs
├── bassi_config.yaml          ← Company config & ICP
├── brochure.pdf               ← Sales brochure (used in outreach)
├── Logo.png                   ← Company logo
├── Email_Upload_Template.xlsx ← Excel template for lead upload
├── cli.py                     ← Optional CLI entrypoint
├── .env.example               ← Template for environment variables
├── .gitignore                 ← Git exclusions
├── render.yaml                ← Render blueprint spec
└── requirements.txt           ← Python dependencies
```

---

*Guide generated on 2026-05-21 • For the Bassi Clothing AI Marketing CRM project*
