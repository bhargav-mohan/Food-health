# NutriPulse - Feature Status

## 🟢 Core Features (Working)
- **User Onboarding / Auth**: Simulated via auto-login (demo user) for immediate access.
- **Food Logging (Manual)**: Fully functional with macro and calorie tracking.
- **Food Logging (AI/Image)**: Fully functional via Google Gemini 2.0 Flash integration. 
- **Dashboard & Insights**: Live tracking of daily calorie goals, macro breakdowns (Chart.js), and health scoring.
- **AI Meal Recommendations**: Fully functional via Gemini.

## 🟢 Integrations & Extensions (Completed)
- **Exercise Logging**: Functional (via Dashboard UI).
- **Steps Tracking**: Functional (via Dashboard UI).
- **Spotify Integration**: Functional (Mocked player embeds on connection in settings).
- **Strava Integration**: Functional (Connection toggle in settings).

## 🛠 Database Status
- **Local**: Fully operational using SQLite (`nutripulse.db`).
- **Production (GCP)**: Pending Cloud SQL connection details (requires PostgreSQL instance).

## ⚠️ Known Limitations
- The app is currently built on **Python/Flask**. If strict Next.js/TypeScript rules apply, a rewrite is necessary.
- Gemini AI features require `GEMINI_API_KEY` in the `.env` file to function. Without it, the app gracefully falls back to manual entry.
