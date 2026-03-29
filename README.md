# ⚡ Decision App

A Django-based productivity tool that helps you make decisions in under 60 seconds — and tracks your habits over time.

## Features
- 🧠 **Decision Engine** — Answer 5 questions to get DO IT / DELAY / SKIP / DO SMALL VERSION
- ⚡ **Quick Decide** — One-tap weighted decision when you're in a rush
- ⚖️ **Task Prioritizer** — Compare two tasks using urgency, impact, effort & deadline scoring
- 📊 **Analytics Dashboard** — Weekly charts, productivity score, priority breakdown
- 🔥 **Streak System** — Daily streak tracker with best-streak record
- 🎯 **Daily Goals** — Set and complete up to 5 goals per day
- 🧠 **Smart Suggestions** — 12 behavioural pattern detectors (procrastination, fatigue, neglect, etc.)
- 📌 **Bookmarks** — Save important decisions
- 🔍 **Search & Filter** — Search history by keyword, filter by result or category
- 🗑️ **Delete Decisions** — Remove decisions you no longer need
- ⬇️ **Export CSV** — Download your entire decision history

## Tech Stack
- Python / Django 4.2+
- Tailwind CSS (via CDN) + custom CSS
- Chart.js for analytics
- SQLite (dev) / PostgreSQL (prod)
- WhiteNoise for static files
- Gunicorn for production serving

## Local Setup

```bash
# 1. Clone
git clone https://github.com/AmitSingh045/Decision-App.git
cd Decision-App

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables (copy and edit)
cp .env.example .env
# Edit .env with your SECRET_KEY

# 5. Run migrations
python decision_app/manage.py migrate

# 6. Start server
python decision_app/manage.py runserver
```

Open http://127.0.0.1:8000

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | Insecure default (change!) |
| `DEBUG` | Debug mode | `True` |
| `ALLOWED_HOSTS` | Comma-separated hosts | `localhost,127.0.0.1` |
| `DATABASE_URL` | PostgreSQL URL | SQLite |

## Deploy to Render (Free)

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Set **Build Command**: `./build.sh`
5. Set **Start Command**: `gunicorn decision_app.wsgi --chdir decision_app`
6. Add environment variables: `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS=yourapp.onrender.com`
7. Deploy!

## Running Tests

```bash
python decision_app/manage.py test core accounts
```
