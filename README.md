# ⚡ NutriPulse — AI-Powered Food & Health Website

A Python Flask website for tracking nutrition with AI-powered food recognition using Google Gemini.

## Features

- **Dashboard** — Daily calorie/macro tracking with charts and health score
- **Food Logging** — Manual entry or upload a food photo for instant AI analysis
- **AI Meal Recommendations** — Personalized suggestions based on your daily intake
- **No Login Required** — Start using immediately

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python / Flask |
| Database | SQLite (zero-config) |
| AI | Google Gemini 2.0 Flash |
| Frontend | Jinja2 + Vanilla CSS/JS |
| Charts | Chart.js |

## Quick Start

```bash
# 1. Clone and enter the project
cd Food-health

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Set your Gemini API key for AI features
#    Get a free key at https://aistudio.google.com/apikey
echo "GEMINI_API_KEY=your_key_here" > .env

# 5. Run the website
python app.py
```

Open **http://localhost:5001** in your browser.

## AI Features (Require Gemini API Key)

Without a key, the app works perfectly for manual food logging and dashboard.
With a key, you unlock:

1. **📸 Food Recognition** — Upload a food photo → AI identifies it and fills in nutrition data
2. **🤖 Meal Recommendations** — Get personalized meal suggestions based on today's intake

## Project Structure

```
Food-health/
├── app.py              # Flask routes (no auth, auto-login)
├── models.py           # SQLite database layer
├── ai_service.py       # Gemini API integration
├── requirements.txt    # Python dependencies
├── .env                # Environment variables
├── Dockerfile          # Container deployment
├── static/
│   ├── style.css       # Dark theme design system
│   └── app.js          # Client-side interactions
├── templates/
│   ├── base.html       # Layout with navbar
│   ├── dashboard.html  # Stats, charts, food list
│   ├── food_log.html   # AI upload + manual form
│   └── recommendations.html  # AI meal suggestions
└── uploads/            # Food images (auto-created)
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google AI API key | No (AI features only) |
| `SECRET_KEY` | Flask session secret | No (has default) |
| `PORT` | Server port | No (default: 5001) |

## Deployment (Docker)

```bash
docker build -t nutripulse .
docker run -p 8080:8080 -e GEMINI_API_KEY=your_key nutripulse
```
