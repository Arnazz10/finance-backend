# Zorvyn Finance Dashboard Backend

A FastAPI backend for a finance dashboard with JWT authentication, role-based access control, record management, and analytics endpoints.

## Features
- **User Management**: Registration, admin-created users, role/status updates, and JWT login.
- **Financial Records**: CRUD for income/expense records with filtering by category, type, and date range.
- **Dashboard Analytics**: Summary totals, category totals, recent transactions, and monthly trends.
- **RBAC Middleware**: Permission enforcement at the API layer.
- **Database**: SQLite with SQLAlchemy and additive startup migrations for existing local DBs.
- **Environment-Based Config**: JWT, database URL, and demo seed credentials can be configured with environment variables.

## Tech Stack
- **FastAPI**: Modern, high-performance web framework.
- **SQLAlchemy**: Database ORM.
- **Pydantic v2**: Request/response validation and serialization.
- **JWT**: Secure authentication.

## Setup Instructions

1. **Clone the repository** (if you haven't already).
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   ```
   Update `SECRET_KEY` before using the project outside local demo mode.
4. **Run the application**:
   ```bash
   python -m app.main
   ```
   Or using uvicorn:
   ```bash
   uvicorn app.main:app --reload
   ```
5. **Access the API Documentation**:
   Visit `http://localhost:8000/docs` for the interactive Swagger UI.

## Demo Users

If `SEED_DEMO_DATA=true`, the app creates these users on startup if they do not already exist:

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@demo.local` | `AdminPass123` |
| Analyst | `analyst@demo.local` | `AnalystPass123` |
| Viewer | `viewer@demo.local` | `ViewerPass123` |

## Role Permissions

| Route | Method | Required Role | Description |
|-------|--------|---------------|-------------|
| `/auth/register` | POST | Public | Create a new user |
| `/auth/login` | POST | Public | Get JWT access token |
| `/users/` | GET | Admin | List all users |
| `/users/` | POST | Admin | Create a user |
| `/users/{id}/role` | PATCH | Admin | Update user role/status |
| `/records/` | GET | Analyst+ | List/Filter financial records |
| `/records/` | POST | Analyst+ | Create a new record |
| `/records/{id}` | GET | Analyst+ | Get a single record |
| `/records/{id}` | PUT | Analyst+ | Update a record |
| `/records/{id}` | DELETE | Admin | Soft delete a record |
| `/dashboard/summary` | GET | Viewer+ | Total income, expenses, balance, categories, recent records |
| `/dashboard/category-totals` | GET | Viewer+ | Net total per category |
| `/dashboard/monthly-trends` | GET | Analyst+ | Monthly income/expense trends |

## API Details
- **Filtering**: `/records/` supports `category`, `type`, `date_from`, and `date_to`.
- **Validation**: Positive amounts, bounded text fields, and date-range validation return proper 4xx responses.
- **Soft Delete**: Deleting a record sets `is_deleted = true` instead of removing it from the database.
- **Auto-Migration**: Startup creates tables and adds a small set of missing SQLite columns for existing local databases.
- **Demo Seed Data**: Startup can seed demo accounts for quick login/testing via environment variables.
- **Verification**: Run `venv/bin/python -m unittest -v tests.test_api` to execute the local test suite.
