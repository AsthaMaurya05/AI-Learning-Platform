# AI Learning Platform

A Django-based learning platform with user authentication, quiz flow, AI-assisted recommendations, and weak-area analysis.

## Project Structure

- `backend/` — Django project and app source code
- `backend/templates/` — HTML templates (login, dashboard, quiz, summary, recommendations)
- `backend/users/` — user/auth logic, analytics, question flow, and ML/AI helper modules

## Tech Stack

- Python
- Django
- SQLite (development)

## Quick Start (Local)

1. **Go to project folder**
   ```bash
   cd backend
   ```

2. **Create and activate virtual environment** (if needed)
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install django
   ```

4. **Apply migrations**
   ```bash
   python manage.py migrate
   ```

5. **Run server**
   ```bash
   python manage.py runserver
   ```

6. Open in browser:
   `http://127.0.0.1:8000/`

## Notes

- The development database file is excluded from Git.
- The virtual environment folder is excluded from Git.

## Author

Astha Maurya
