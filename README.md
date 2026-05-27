# ✦ MailMind — AI Email Intelligence Dashboard

A beautiful Streamlit app that connects to your **Outlook inbox**, classifies emails by priority using **Groq AI**, and caches results in **PostgreSQL** — so you never miss what matters.

---

## Features

- 🔗 **Microsoft OAuth** — Secure read-only Outlook access via Microsoft Graph API
- ⚡ **Groq AI Classification** — Every email ranked as High / Medium / Low priority
- 📝 **Smart Summaries** — One-line TL;DR for every email
- 🗄️ **PostgreSQL Caching** — Aiven-hosted DB so re-runs are instant
- 📅 **Flexible Date Ranges** — Today, Last Week, or custom date picker
- 🎨 **Beautiful UI** — Editorial newspaper aesthetic, fully responsive

---

## Setup Guide

### Step 1: Register Microsoft Azure App

1. Go to [Azure Portal → App Registrations](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps)
2. Click **New registration**
3. Name: `MailMind` (or anything)
4. Supported account types: **Accounts in any organizational directory and personal Microsoft accounts**
5. Redirect URI: `http://localhost:8501` (type: Web)
6. Click **Register**
7. Copy **Application (client) ID** → `MS_CLIENT_ID`
8. Go to **Certificates & secrets** → New client secret → Copy value → `MS_CLIENT_SECRET`
9. Go to **API permissions** → Add:
   - `Microsoft Graph` → Delegated → `Mail.Read`
   - `Microsoft Graph` → Delegated → `User.Read`
10. Click **Grant admin consent**

### Step 2: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and fill in all values.

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Run the App

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Project Structure

```
email-dashboard/
├── app.py                  # Entry point + login page
├── pages/
│   └── dashboard.py        # Main email dashboard
├── utils/
│   ├── auth.py             # Microsoft OAuth (MSAL)
│   ├── db.py               # PostgreSQL operations
│   ├── graph.py            # Microsoft Graph email fetcher
│   └── ai.py               # Groq AI classifier + summarizer
├── .streamlit/
│   └── config.toml         # Theme config
├── requirements.txt
├── .env.example
└── README.md
```

---

## How It Works

1. **Login** — OAuth redirect to Microsoft, token stored in session
2. **Select dates** — Sidebar quick-select or custom range
3. **Fetch** — Microsoft Graph API pulls emails for the period
4. **AI Analysis** — Groq (Llama3-70B) classifies + summarizes each email
5. **Cache** — Results stored in PostgreSQL (Aiven)
6. **Display** — Emails shown in priority sections with full summaries

---

## Environment Variables

| Variable | Description |
|---|---|
| `MS_CLIENT_ID` | Azure App Client ID |
| `MS_CLIENT_SECRET` | Azure App Client Secret |
| `MS_TENANT_ID` | `common` for personal + org accounts |
| `REDIRECT_URI` | `http://localhost:8501` |
| `GROQ_API_KEY` | From [console.groq.com](https://console.groq.com) |
| `DB_HOST` | Aiven PostgreSQL host |
| `DB_NAME` | Database name (`defaultdb`) |
| `DB_USER` | Database user |
| `DB_PASSWORD` | Database password |
| `DB_PORT` | Database port |

---

## Tips

- **Force Re-fetch**: Check "Force re-fetch from Outlook" in sidebar to bypass cache
- **SSL**: Aiven requires `sslmode=require` — already handled in `db.py`
- **Rate limits**: Groq free tier is very generous; 100 emails will process in ~30s
- **Pagination**: App handles Outlook's 100-email-per-page limit automatically
