# Finance Dashboard API

A clean, well-structured backend for a finance dashboard built with **FastAPI**, **SQLAlchemy (SQLite)**, **JWT authentication**, and **Redis** for caching and rate limiting.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Project Structure](#project-structure)
3. [Setup Instructions](#setup-instructions)
4. [Environment Variables](#environment-variables)
5. [Database Setup](#database-setup)
6. [Redis Setup](#redis-setup)
7. [Running the App](#running-the-app)
8. [Authentication Flow](#authentication-flow)
9. [Role Permissions](#role-permissions)
10. [API Reference](#api-reference)

---

## Project Overview

This API powers a finance dashboard with:

- **JWT Authentication** — access tokens (30 min) + refresh tokens (7 days)
- **Role-Based Access Control** — Viewer, Analyst, Admin with clean decorator-based enforcement
- **Financial Records** — create, read, update, soft-delete income/expense entries
- **Dashboard Summaries** — totals, trends, and category breakdowns, cached in Redis
- **Rate Limiting** — Redis-backed sliding-window limiter (60 req/min per IP by default)
- **Graceful Redis Degradation** — if Redis is unavailable, the app still works (caching and rate limiting are skipped)

---

## Project Structure

```
finance-dashboard/
├── app/
│   ├── main.py                  # App factory, router registration, error handlers
│   ├── core/
│   │   ├── auth.py              # FastAPI dependency: get_current_user
│   │   ├── config.py            # Settings loaded from .env via pydantic-settings
│   │   ├── decorators.py        # @require_roles, @require_admin, etc.
│   │   └── security.py          # Password hashing, JWT encode/decode
│   ├── db/
│   │   ├── session.py           # SQLAlchemy engine, SessionLocal, get_db dependency
│   │   └── init_db.py           # Table creation + default admin seeding
│   ├── models/
│   │   ├── user.py              # User ORM model + UserRole enum
│   │   └── financial_record.py  # FinancialRecord ORM model + RecordType enum
│   ├── schemas/
│   │   ├── user.py              # Pydantic schemas: UserCreate, UserResponse, TokenResponse, …
│   │   ├── financial_record.py  # RecordCreate, RecordUpdate, RecordResponse, RecordFilter
│   │   └── dashboard.py         # DashboardSummary, CategoryTotal, MonthlyTrend
│   ├── routes/
│   │   ├── auth.py              # POST /auth/login, POST /auth/refresh
│   │   ├── users.py             # CRUD /users/
│   │   ├── records.py           # CRUD /records/
│   │   └── dashboard.py         # GET /dashboard/summary|income|expenses|…
│   ├── services/
│   │   ├── user_service.py      # User DB operations (create, authenticate, update, …)
│   │   ├── record_service.py    # Record DB operations (CRUD, soft delete, filtering)
│   │   └── dashboard_service.py # Aggregate queries (totals, trends, categories)
│   └── utils/
│       ├── redis_client.py      # Async Redis helpers: cache_get, cache_set, cache_delete_pattern
│       └── rate_limiter.py      # FastAPI dependency: rate_limit
├── requirements.txt
├── .env.example
└── README.md
```

---

## Setup Instructions

### Prerequisites

- Python 3.11+
- Redis (local or remote)
- pip

### Step 1 — Clone and enter the project

```bash
git clone <repo-url>
cd finance-dashboard
```

### Step 2 — Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Configure environment

```bash
cp .env.example .env
# Open .env and update SECRET_KEY (and REDIS_URL if needed)
```

---

## Environment Variables

| Variable                    | Default                              | Description                                 |
|-----------------------------|--------------------------------------|---------------------------------------------|
| `APP_NAME`                  | `Finance Dashboard API`              | Application display name                    |
| `APP_ENV`                   | `development`                        | Environment tag                             |
| `DEBUG`                     | `true`                               | Show tracebacks; enable /docs               |
| `SECRET_KEY`                | *(must change)*                      | JWT signing secret — use a long random str  |
| `ALGORITHM`                 | `HS256`                              | JWT algorithm                               |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30`                               | Access token lifetime                       |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7`                                  | Refresh token lifetime                      |
| `DATABASE_URL`              | `sqlite:///./finance_dashboard.db`   | SQLAlchemy DB URL                           |
| `REDIS_URL`                 | `redis://localhost:6379/0`           | Redis connection string                     |
| `RATE_LIMIT_REQUESTS`       | `60`                                 | Max requests per window per IP              |
| `RATE_LIMIT_WINDOW`         | `60`                                 | Window size in seconds                      |

---

## Database Setup

SQLite is used — no server required. The database file is created automatically on first run.

Tables are created and a default admin is seeded at startup:

```
Email:    admin@example.com
Password: Admin@1234
```

**Change the admin password immediately after first login.**

If you want to reset the database:

```bash
rm finance_dashboard.db
# Restart the app — tables and default admin are re-created
```

---

## Redis Setup

### macOS

```bash
brew install redis
brew services start redis
```

### Ubuntu / Debian

```bash
sudo apt install redis-server
sudo systemctl start redis
```

### Docker

```bash
docker run -d -p 6379:6379 redis:7-alpine
```

### Verify Redis is running

```bash
redis-cli ping
# Expected: PONG
```

> **Note:** If Redis is unavailable, the app still starts and works normally.  
> Caching and rate limiting are silently skipped until Redis comes back up.

---

## Running the App

```bash
uvicorn app.main:app --reload
```

The API will be available at: `http://localhost:8000`

Interactive docs (dev mode only): `http://localhost:8000/docs`

Health check: `http://localhost:8000/health`

---

## Authentication Flow

```
1. POST /api/v1/auth/login
   → Provide email + password
   → Receive access_token (30 min) + refresh_token (7 days)

2. Include access_token in every protected request:
   Authorization: Bearer <access_token>

3. When the access token expires:
   POST /api/v1/auth/refresh
   → Provide refresh_token
   → Receive a new access_token + refresh_token pair

4. Refresh tokens are single-use by convention (each refresh issues a new pair).
   Store the latest refresh_token securely on the client.
```

Tokens carry the user's `id` and `role` in their payload. The server validates the signature and expiry on every request — no session state is stored server-side.

---

## Role Permissions

| Endpoint group          | Viewer | Analyst | Admin |
|-------------------------|:------:|:-------:|:-----:|
| GET /dashboard/summary  | ✅     | ✅      | ✅    |
| GET /dashboard/recent   | ✅     | ✅      | ✅    |
| GET /dashboard/income   | ❌     | ✅      | ✅    |
| GET /dashboard/expenses | ❌     | ✅      | ✅    |
| GET /dashboard/net-balance | ❌  | ✅      | ✅    |
| GET /dashboard/categories | ❌   | ✅      | ✅    |
| GET /dashboard/trends   | ❌     | ✅      | ✅    |
| GET /records/           | ✅     | ✅      | ✅    |
| GET /records/{id}       | ✅     | ✅      | ✅    |
| POST /records/          | ❌     | ❌      | ✅    |
| PATCH /records/{id}     | ❌     | ❌      | ✅    |
| DELETE /records/{id}    | ❌     | ❌      | ✅    |
| GET /users/me           | ✅     | ✅      | ✅    |
| All other /users/*      | ❌     | ❌      | ✅    |

---

## API Reference

All endpoints are prefixed with `/api/v1`.  
Protected endpoints require: `Authorization: Bearer <access_token>`

---

### Auth

---

#### `POST /api/v1/auth/login`

Authenticate and receive tokens.

**Request:**
```json
{
  "email": "admin@example.com",
  "password": "Admin@1234"
}
```

**Response `200`:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Errors:** `401` wrong credentials · `403` inactive account · `429` rate limit

---

#### `POST /api/v1/auth/refresh`

Exchange a refresh token for a new token pair.

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response `200`:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Errors:** `401` invalid/expired refresh token

---

### Users *(Admin only, except `/me`)*

---

#### `POST /api/v1/users/`

Create a new user.

**Request:**
```json
{
  "email": "analyst@example.com",
  "full_name": "Jane Analyst",
  "password": "Secure@99",
  "role": "analyst"
}
```

**Response `201`:**
```json
{
  "id": 2,
  "email": "analyst@example.com",
  "full_name": "Jane Analyst",
  "role": "analyst",
  "is_active": true,
  "created_at": "2024-11-01T10:00:00Z"
}
```

**Errors:** `409` email already exists · `422` validation error · `403` not admin

---

#### `GET /api/v1/users/`

List all users.

**Response `200`:**
```json
[
  {
    "id": 1,
    "email": "admin@example.com",
    "full_name": "System Admin",
    "role": "admin",
    "is_active": true,
    "created_at": "2024-11-01T09:00:00Z"
  }
]
```

---

#### `GET /api/v1/users/me`

Get the currently authenticated user's profile. Available to all roles.

**Response `200`:**
```json
{
  "id": 2,
  "email": "analyst@example.com",
  "full_name": "Jane Analyst",
  "role": "analyst",
  "is_active": true,
  "created_at": "2024-11-01T10:00:00Z"
}
```

---

#### `GET /api/v1/users/{user_id}`

Retrieve a specific user by ID.

**Response `200`:** *(same shape as above)*

**Errors:** `404` not found

---

#### `PATCH /api/v1/users/{user_id}`

Update a user's role, name, or active status. All fields optional.

**Request:**
```json
{
  "role": "viewer",
  "is_active": false
}
```

**Response `200`:** *(updated user object)*

---

#### `DELETE /api/v1/users/{user_id}`

Hard-delete a user. Prefer deactivation (`is_active: false`) over deletion.

**Response `204`:** No content

---

### Financial Records

---

#### `POST /api/v1/records/`

Create a financial record. *(Admin only)*

**Request:**
```json
{
  "amount": 5000.00,
  "type": "income",
  "category": "salary",
  "date": "2024-11-01",
  "notes": "November salary"
}
```

**Response `201`:**
```json
{
  "id": 1,
  "amount": 5000.0,
  "type": "income",
  "category": "salary",
  "date": "2024-11-01",
  "notes": "November salary",
  "created_at": "2024-11-01T10:05:00Z",
  "updated_at": "2024-11-01T10:05:00Z"
}
```

**Errors:** `422` validation error · `403` not admin

---

#### `GET /api/v1/records/`

List records with optional filters. *(Viewer+)*

**Query parameters:**

| Param       | Type   | Example        | Description              |
|-------------|--------|----------------|--------------------------|
| `type`      | string | `income`       | Filter by record type    |
| `category`  | string | `salary`       | Filter by category       |
| `date_from` | date   | `2024-01-01`   | Start of date range      |
| `date_to`   | date   | `2024-12-31`   | End of date range        |
| `limit`     | int    | `50`           | Page size (default 100)  |
| `offset`    | int    | `0`            | Pagination offset        |

**Response `200`:**
```json
[
  {
    "id": 1,
    "amount": 5000.0,
    "type": "income",
    "category": "salary",
    "date": "2024-11-01",
    "notes": "November salary",
    "created_at": "2024-11-01T10:05:00Z",
    "updated_at": "2024-11-01T10:05:00Z"
  }
]
```

---

#### `GET /api/v1/records/{record_id}`

Retrieve a single record. *(Viewer+)*

**Response `200`:** *(single record object)*

**Errors:** `404` not found

---

#### `PATCH /api/v1/records/{record_id}`

Update a record. All fields optional. *(Admin only)*

**Request:**
```json
{
  "amount": 5200.00,
  "notes": "November salary + bonus"
}
```

**Response `200`:** *(updated record object)*

---

#### `DELETE /api/v1/records/{record_id}`

Soft-delete a record (hidden from all queries, row kept in DB). *(Admin only)*

**Response `204`:** No content

---

### Dashboard

---

#### `GET /api/v1/dashboard/summary`

Full dashboard overview in one call. *(Viewer+)* — **Cached 5 min**

**Response `200`:**
```json
{
  "total_income": 15000.0,
  "total_expenses": 8400.0,
  "net_balance": 6600.0,
  "category_totals": [
    { "category": "salary", "total": 15000.0 },
    { "category": "rent",   "total": 4500.0 },
    { "category": "food",   "total": 1200.0 }
  ],
  "recent_transactions": [
    {
      "id": 3,
      "amount": 1200.0,
      "type": "expense",
      "category": "food",
      "date": "2024-11-10",
      "notes": null,
      "created_at": "2024-11-10T08:00:00Z",
      "updated_at": "2024-11-10T08:00:00Z"
    }
  ]
}
```

---

#### `GET /api/v1/dashboard/income`

Total income. *(Analyst+)* — **Cached 5 min**

**Response `200`:**
```json
{ "total_income": 15000.0 }
```

---

#### `GET /api/v1/dashboard/expenses`

Total expenses. *(Analyst+)* — **Cached 5 min**

**Response `200`:**
```json
{ "total_expenses": 8400.0 }
```

---

#### `GET /api/v1/dashboard/net-balance`

Net balance breakdown. *(Analyst+)* — **Cached 5 min**

**Response `200`:**
```json
{
  "total_income": 15000.0,
  "total_expenses": 8400.0,
  "net_balance": 6600.0
}
```

---

#### `GET /api/v1/dashboard/categories`

Amounts grouped by category. *(Analyst+)* — **Cached 5 min**

**Response `200`:**
```json
[
  { "category": "salary", "total": 15000.0 },
  { "category": "rent",   "total": 4500.0 },
  { "category": "food",   "total": 1200.0 }
]
```

---

#### `GET /api/v1/dashboard/recent`

Most recent transactions. *(Viewer+)*

**Query parameter:** `limit` (1–50, default 10)

**Response `200`:** *(array of record objects)*

---

#### `GET /api/v1/dashboard/trends`

Monthly income vs expense trends. *(Analyst+)* — **Cached 5 min**

**Query parameter:** `months` (1–60, default 12)

**Response `200`:**
```json
[
  {
    "year": 2024,
    "month": 10,
    "income": 5000.0,
    "expense": 2800.0,
    "net": 2200.0
  },
  {
    "year": 2024,
    "month": 11,
    "income": 5000.0,
    "expense": 2900.0,
    "net": 2100.0
  }
]
```

---

## Common Error Responses

```json
// 401 Unauthorized
{ "detail": "Invalid or expired access token." }

// 403 Forbidden
{ "detail": "Access denied. Required roles: admin." }

// 404 Not Found
{ "detail": "Record not found." }

// 409 Conflict
{ "detail": "A user with email 'x@y.com' already exists." }

// 422 Validation Error
{
  "detail": "Validation failed.",
  "errors": [
    { "field": "body → amount", "message": "Amount must be greater than zero." }
  ]
}

// 429 Too Many Requests
{ "detail": "Rate limit exceeded. Max 60 requests per 60 seconds." }
```
