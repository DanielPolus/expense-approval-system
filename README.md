# Expense Approval System

A backend API for managing and approving employee expenses.

The project implements a real-world expense approval workflow with role-based access control, JWT authentication, audit logging, PostgreSQL, automated tests, Docker, and a working deployment on Azure Container Apps.
## Features

- User registration and authentication with JWT
- Role-based access control:
  - Employee
  - Manager
  - Accountant
- Expense creation and management
- Expense filtering by status and category
- Pagination
- Approval workflow
- Audit trail for expense actions
- PostgreSQL persistence
- Alembic migrations
- Dockerized application
- Automated API tests with pytest
- Container image build and publishing through GitHub Actions and GitHub Container Registry
- Tested deployment to Azure Container Apps using the Consumption workload profile

## Expense workflow

```text
DRAFT -> SUBMITTED -> APPROVED -> PAID
                    \-> REJECTED
```

### Employee

- Create an expense
- View own expenses
- Update or delete own expenses while they are in `DRAFT`
- Submit an expense for approval

### Manager

- View all expenses
- Approve submitted expenses
- Reject submitted expenses

### Accountant

- View all expenses
- Mark approved expenses as paid

Every important action is recorded in the expense audit trail.

## Tech stack

- Python 3.11
- FastAPI
- SQLAlchemy 2
- PostgreSQL
- Alembic
- Pydantic
- JWT authentication
- Argon2 password hashing
- Pytest
- Docker / Docker Compose
- GitHub Actions
- GitHub Container Registry
- Azure Container Apps

## Project structure

```text
app/
├── api/
│   ├── dependencies.py
│   ├── auth.py
│   └── expenses.py
├── core/
│   ├── config.py
│   └── security.py
├── db/
│   ├── base.py
│   └── session.py
├── models/
├── schemas/
├── tests/
└── main.py

alembic/
Dockerfile
compose.yaml
start.sh
requirements.txt
.env.example
```

## Running locally

### 1. Clone the repository

```bash
git clone https://github.com/DanielPolus/expense-approval-system.git
cd expense-approval-system
```

### 2. Create the environment file

Copy `.env.example` to `.env` and provide your local configuration.

Example:

```env
DATABASE_URL=postgresql+psycopg://expense_user:expense_password@localhost:5432/expense_db
TEST_DATABASE_URL=postgresql+psycopg://expense_user:expense_password@localhost:5432/expense_test_db

JWT_SECRET_KEY=replace_with_a_long_random_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Generate a JWT secret, for example:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### 3. Start PostgreSQL and the API with Docker

```bash
docker compose up --build
```

The API will be available at:

```text
http://localhost:8000
```

Swagger UI:

```text
http://localhost:8000/docs
```

Health endpoint:

```text
http://localhost:8000/health
```

## Database migrations

Apply migrations manually with:

```bash
python -m alembic upgrade head
```

The Docker startup script also applies migrations before starting Uvicorn.

## Tests

The project includes API tests for authentication, permissions, ownership rules, expense lifecycle transitions, and audit logging.

Run:

```bash
pytest
```

Current test suite:

```text
10 passed
```

## Main API endpoints

### Authentication

```text
POST /auth/register
POST /auth/login
GET  /auth/me
```

### Expenses

```text
POST   /expenses
GET    /expenses
GET    /expenses/{expense_id}
PATCH  /expenses/{expense_id}
DELETE /expenses/{expense_id}

POST /expenses/{expense_id}/submit
POST /expenses/{expense_id}/approve
POST /expenses/{expense_id}/reject
POST /expenses/{expense_id}/pay

GET /expenses/{expense_id}/audit
```

## Azure deployment

The application was deployed and tested on **Azure Container Apps**.

Deployment setup:

```text
GitHub repository
        ↓
GitHub Actions
        ↓
GitHub Container Registry
        ↓
Azure Container Apps
```

The deployment used:

- Azure Container Apps
- Consumption workload profile
- 0.25 vCPU / 0.5 GiB
- Public HTTPS ingress
- Target port `8000`
- Environment-based application configuration
- Docker image hosted in GitHub Container Registry

For the short-lived Azure deployment test, an ephemeral SQLite database was used inside the container instead of provisioning a separate cloud PostgreSQL service. The main application configuration and local Docker environment use PostgreSQL.

The deployed API was tested through its public HTTPS endpoint, including:

- health check
- Swagger UI
- registration
- JWT authentication
- expense creation
- expense listing
- expense submission
- permission validation
- audit trail retrieval

The Azure resources were removed after testing.

## Example expense

```json
{
  "title": "Software subscription",
  "details": "Monthly development tool subscription",
  "amount": 25.50,
  "currency": "EUR",
  "category": "software"
}
```

## Business rules

The API enforces workflow rules at the backend level.

Examples:

- employees cannot approve expenses;
- managers cannot mark expenses as paid;
- accountants can only pay approved expenses;
- submitted expenses cannot be edited by employees;
- employees cannot access expenses belonging to other employees;
- only valid status transitions are accepted.

## Repository

https://github.com/DanielPolus/expense-approval-system
