# Taska

A full-stack task management app built with FastAPI and React.

## Tech Stack

**Backend**
- Python, FastAPI, PostgreSQL
- SQLAlchemy ORM, Alembic migrations
- JWT authentication, bcrypt password hashing

**Frontend**
- React 19, TypeScript, Vite
- Tailwind CSS v4
- Axios, React Router

## Features

- Register and log in with JWT-based auth
- Create, edit, delete and complete tasks
- Filter by status and priority, sort by date or priority
- Search tasks by title or description
- Stats dashboard — total, pending, completed, overdue
- Dark / light / system theme
- Change password in settings
- Toast notifications and confirm-before-delete

## Running locally

**Requirements:** Docker, Python 3.11+, Node 18+

```bash
# 1. Start the database
docker compose up -d

# 2. Start the backend
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# 3. Start the frontend
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`

## Project structure

```
task-manager/
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── routers/
│   │   └── core/
│   ├── alembic/
│   └── requirements.txt
└── frontend/
    └── src/
        ├── api/
        ├── components/
        ├── hooks/
        ├── pages/
        └── types/
```

## Environment variables

Create `backend/.env`:
```
DATABASE_URL=postgresql://postgres:password@localhost:5433/taskmanager
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Create `frontend/.env`:
```
VITE_API_URL=http://localhost:8000
```
