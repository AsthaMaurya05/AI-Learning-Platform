# AI Learning Platform

AI Learning Platform is a Django web application for aptitude practice and personalized learning.
It combines:

- user authentication with email OTP verification,
- static quiz practice,
- adaptive AI-generated quizzes,
- weak-area analytics,
- recommendation-driven practice navigation.

The project is designed as a monolithic Django app for easy local development and iterative feature growth.

---

## Core Features

### 1) Authentication + Email OTP Verification

- Users register with username, email, and password.
- New accounts are created as inactive (`is_active=False`).
- A 6-digit OTP is generated, stored in session (10-minute expiry), and sent via email backend.
- User verifies OTP to activate account.
- If an unverified user tries to log in, OTP flow is triggered again.

Security checks included:

- password validation with Django validators,
- OTP attempt counting (lock after too many tries),
- safe redirect handling for `next` URL.

### 2) Static Quiz Practice (Question Bank)

- Beginner-friendly static questions are defined in `users/questions.py`.
- Questions are shuffled per session.
- Each attempt stores:
  - selected option,
  - correctness,
  - topic,
  - difficulty,
  - time taken.
- Quiz summary computes accuracy and timing stats.

### 3) Adaptive AI Quiz

- Adaptive mode generates fresh questions dynamically using Groq API.
- If no API key is available (or API fails), the system falls back to static questions.
- Questions are generated based on weakest topic and estimated user level.
- Adaptive sessions are kept in Django session state and saved as `PracticeActivity` attempts.

### 4) Weak Area Analysis

Analytics pipeline computes per-topic performance using:

- accuracy,
- average response time,
- consistency over recent attempts.

These are combined into a weighted weakness score:

- Accuracy weight: 50%
- Time weight: 30%
- Consistency weight: 20%

Topics are classified as `Strong`, `Moderate`, or `Weak`, and sorted by weakness score.

### 5) Personalized Recommendations

Recommendation engine groups topics into:

- High priority
- Medium priority
- Maintain

Each topic recommendation includes a reason + targeted practice suggestion.

### 6) Performance Dashboard

The dashboard uses stored attempts/sessions to show:

- total attempted questions,
- overall accuracy,
- average time per question,
- weak topic count,
- topic-wise accuracy,
- recent quiz sessions,
- accuracy trend data.

---

## How the App Works (Flow)

### User Journey

1. Register account
2. Verify email OTP
3. Login
4. Open dashboard
5. Click Practice
   - first-time user → static quiz
   - returning user → recommendation page
6. Attempt quiz (static or adaptive)
7. View summary and updated analytics
8. Open weak-areas/recommendations for next targeted practice

### Practice Routing Logic

`/practice/` checks if user has prior `PracticeActivity` rows:

- no history → redirect to `/quiz/`
- has history → redirect to `/recommendations/`

---

## Architecture Overview

### Backend Stack

- Python 3
- Django 6
- SQLite (default development DB)
- Groq Python SDK (for AI question generation)

### Django App Layout

- `backend/backend/`
  - project settings, root URLs, WSGI/ASGI
- `backend/users/`
  - authentication flows
  - quiz logic
  - analytics + recommendations
  - AI generation integration
  - database models
- `backend/templates/`
  - UI templates for auth, dashboard, quiz, summary, weak areas, recommendations

---

## Data Model

### `PracticeActivity`

Stores every attempted question.

Fields include:

- user (FK)
- question_id
- topic
- difficulty
- selected_option
- correct_answer
- is_correct
- time_taken (seconds)
- attempted_at

Use cases:

- topic analytics
- weak area detection
- adaptive topic selection

### `QuizSession`

Stores aggregate session-level summary.

Fields include:

- user (FK)
- total_questions
- correct_answers
- accuracy
- total_time
- completed_at

Use cases:

- dashboard trend chart
- recent session history

---

## Important Routes

- `/` → redirects to login
- `/login/` → login
- `/register/` → registration
- `/verify-email-otp/` → OTP verification
- `/resend-email-otp/` → resend OTP
- `/dashboard/` → dashboard analytics
- `/practice/` → intelligent practice entry
- `/quiz/` → static quiz flow
- `/quiz/summary/` → static quiz summary
- `/weak-areas/` → weakness analysis page
- `/recommendations/` → personalized recommendation page
- `/adaptive-quiz/` → AI/adaptive quiz flow
- `/adaptive-quiz/summary/` → adaptive summary
- `/logout/` → logout (POST)

---

## Setup and Run (Local)

### 1) Clone and move to project

```bash
git clone https://github.com/AsthaMaurya05/AI-Learning-Platform.git
cd AI-Learning-Platform/backend
```

### 2) Create virtual environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

### 3) Install dependencies

```bash
pip install django groq
```

### 4) Run migrations

```bash
python manage.py migrate
```

### 5) Start server

```bash
python manage.py runserver
```

Open: `http://127.0.0.1:8000/`

---

## Environment Variables

The project reads configuration from environment variables:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `GROQ_API_KEY`
- `DEFAULT_FROM_EMAIL`
- `EMAIL_BACKEND`
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `EMAIL_USE_TLS`

### Notes

- If `GROQ_API_KEY` is missing, AI generation gracefully falls back to static questions.
- Default email backend is console backend for local development.

---

## Current Scope and Limitations

- SQLite is used for development simplicity.
- UI is template-based (no SPA frontend).
- Adaptive summary currently stores accuracy but not total time analytics.
- AI generation quality depends on API availability/response validity.

---

## Future Enhancements

- Add `requirements.txt`/`pyproject.toml` for reproducible dependency installs.
- Add automated tests for auth/quiz/analytics endpoints.
- Add production deployment config (PostgreSQL + static/media strategy).
- Add richer dashboard visualizations and topic progression history.

---

## Author

Astha Maurya
