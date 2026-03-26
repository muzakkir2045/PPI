# 🧠 Personal Progress Intelligence

> **Most people don't know which of their work habits actually make them productive.**
> PPI tracks your work sessions and tells you — with data, not guesses.

🔗 **[Live Demo](https://ppi-f69t.onrender.com)**

---

## What is PPI?

Personal Progress Intelligence is a full-stack Flask web app that lets you log work sessions across your projects and then analyzes your patterns to give you **personalized, data-driven productivity insights.**

Not generic tips. Insights based on *your* data — like:
- *"Your 45–60 minute sessions consistently produce the best outcomes"*
- *"Long sessions frequently end without documented results — try shorter sprints"*
- *"You document outcomes only 40% of the time — this makes it harder to track progress"*

---

## Features

### Core
- **User Authentication** — Secure registration and login with PBKDF2-SHA256 password hashing
- **Project Management** — Create, edit, and track multiple projects with status tracking
- **Work Session Logging** — Log sessions with start/end time, duration, description, and outcome notes

### Smart Insights Engine
The heart of PPI lives in `metrics.py`. It analyzes your session history and surfaces:

| Insight Type | What it tells you |
|---|---|
| **Effectiveness** | Which session lengths produce your best outcomes |
| **Reliability** | How consistently you document what you achieved |
| **Observations** | Patterns you wouldn't notice manually |
| **Recommendations** | Specific, actionable next steps |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web Framework | Flask |
| ORM | SQLAlchemy + Flask-Migrate |
| Auth | Flask-Login + Werkzeug |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Deployment | Render (auto-detects PostgreSQL, SSL configured) |

---

## Project Structure

```
personal-progress-intelligence/
│
├── app/
│   ├── main.py        # Routes and app configuration
│   ├── models.py      # User, Project, WorkSession models
│   ├── metrics.py     # Analytics and insights engine ← the interesting part
│   └── utils.py       # Input validation helpers
│
├── templates/         # Jinja2 HTML templates
├── static/            # CSS and assets
├── migrations/        # Flask-Migrate database migrations
└── .env               # Environment variables (gitignored)
```

---

## Getting Started

```bash
git clone https://github.com/muzakkir2045/PPI.git
cd PPI
pip install -r requirements.txt
```

Create a `.env` file:
```
SECRET_KEY=your_secret_key
DATABASE_URL=sqlite:///instance/database.db   # or your PostgreSQL URL
```

Run the app:
```bash
flask db upgrade
flask run
```

Visit `http://localhost:5000`

---

## How the Insights Engine Works

The `WorkSession` model stores timing, description, and outcome for every session. `metrics.py` then:

1. Groups sessions by duration bucket (short / medium / long)
2. Scores each bucket by outcome documentation rate
3. Compares effectiveness across session types
4. Generates natural-language observations and recommendations

This is the core value of PPI — not just storing data, but making it useful.

---

## Deployment

Configured for Railway or Render:
- Auto-detects `DATABASE_URL` for PostgreSQL
- SSL mode enabled for production databases
- SQLAlchemy connection pooling with pre-ping health checks

---

*Built with Flask, SQLAlchemy, and the genuine desire to understand my own productivity.*
