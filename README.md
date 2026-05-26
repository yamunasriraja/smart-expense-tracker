# Smart Expense Tracker

A full-stack web application for tracking personal expenses, built with
Python Django. Designed as a professional portfolio project.

## Features

- **User Authentication** — Register, login, logout with session management
- **Expense Management** — Add, edit, delete, and view all expenses
- **Categories** — 10 built-in categories with icons and colour badges
- **Dashboard Analytics** — Live stat cards, Chart.js pie and line charts
- **Monthly Budget** — Set a budget limit with a real-time progress bar
- **Smart Insights** — Automated alerts for overspending and trends
- **CSV Export** — Download all expenses as a spreadsheet
- **Search** — Find expenses by description or category
- **Responsive UI** — Bootstrap 5 sidebar layout, works on all screen sizes

## Tech Stack

| Layer      | Technology              |
|------------|-------------------------|
| Backend    | Python 3.x + Django 5.x |
| Database   | SQLite (dev)            |
| Frontend   | HTML5, CSS3, Bootstrap 5|
| Charts     | Chart.js 4.x            |
| Icons      | Bootstrap Icons         |
| Fonts      | Google Fonts (Inter)    |

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/smart-expense-tracker.git
cd smart-expense-tracker

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Apply database migrations
python manage.py migrate

# 5. Create an admin account
python manage.py createsuperuser

# 6. Run the development server
python manage.py runserver
```

Visit http://127.0.0.1:8000 to use the app.
Visit http://127.0.0.1:8000/admin for the admin panel.

## Project Structure