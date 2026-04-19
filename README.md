# Task Manager — Backend Build Log

A detailed, step-by-step explanation of everything that has been built so far, with real examples from the actual code.

---

## Table of Contents

1. [Project Structure (what exists now)](#1-project-structure)
2. [Step 1 — Database with Docker Compose](#2-step-1--database-with-docker-compose)
3. [Step 2 — Connecting Python to the Database](#3-step-2--connecting-python-to-the-database)
4. [Step 3 — Reading Config from the .env File](#4-step-3--reading-config-from-the-env-file)
5. [Step 4 — ORM Models (Database Tables as Python Classes)](#5-step-4--orm-models-database-tables-as-python-classes)
6. [Step 5 — Alembic Migrations (Creating the Tables)](#6-step-5--alembic-migrations-creating-the-tables)
7. [Step 6 — Password Hashing and JWT Tokens](#7-step-6--password-hashing-and-jwt-tokens)
8. [Step 7 — Dependencies (get_db and get_current_user)](#8-step-7--dependencies-get_db-and-get_current_user)
9. [Step 8 — Pydantic Schemas (Validating Request and Response Data)](#9-step-8--pydantic-schemas-validating-request-and-response-data)
10. [Step 9 — Auth Routes (Register, Login, Me)](#10-step-9--auth-routes-register-login-me)
11. [Step 10 — Task Routes (Full CRUD + Stats)](#11-step-10--task-routes-full-crud--stats)
12. [Step 11 — Wiring Everything Together in main.py](#12-step-11--wiring-everything-together-in-mainpy)
13. [How a Real Request Flows Through the App](#13-how-a-real-request-flows-through-the-app)
14. [How to Start the Backend](#14-how-to-start-the-backend)
15. [Port Conflict Fix Explained](#15-port-conflict-fix-explained)

---

## 1. Project Structure

This is the current state of the backend folder:

```
task-manager/
├── docker-compose.yml          # Starts the PostgreSQL database in Docker
├── backend/
│   ├── .env                    # Secret config values (NOT committed to git)
│   ├── requirements.txt        # All Python packages used
│   ├── alembic.ini             # Alembic configuration file
│   ├── alembic/
│   │   ├── env.py              # Tells Alembic how to connect and what models to scan
│   │   └── versions/
│   │       └── f4e4ae5cab83_create_users_and_tasks_tables.py  # The migration script
│   └── app/
│       ├── main.py             # FastAPI app entry point
│       ├── config.py           # Reads .env file into a typed Settings object
│       ├── database.py         # SQLAlchemy engine and session factory
│       ├── models/
│       │   ├── user.py         # User table definition
│       │   └── task.py         # Task table definition
│       ├── schemas/
│       │   ├── user.py         # What data is accepted/returned for users
│       │   └── task.py         # What data is accepted/returned for tasks
│       ├── core/
│       │   ├── security.py     # Password hashing and JWT creation/verification
│       │   └── deps.py         # Reusable FastAPI dependencies
│       └── routers/
│           ├── auth.py         # /auth/register, /auth/token, /auth/me
│           └── tasks.py        # All /tasks/ endpoints
```

---

## 2. Step 1 — Database with Docker Compose

**File:** `docker-compose.yml`

Instead of installing PostgreSQL directly on your machine, Docker runs it inside a container. Think of a container as a sealed box with its own operating system, software, and data — completely separate from your machine.

```yaml
services:
  db:
    image: postgres:15          # Use the official PostgreSQL 15 image
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: taskmanager  # Creates this database automatically on first start
    ports:
      - '5433:5432'             # Map host port 5433 → container port 5432
    volumes:
      - postgres_data:/var/lib/postgresql/data  # Data persists even if container restarts

volumes:
  postgres_data:                # Named volume — Docker manages where this lives on disk
```

**Why port 5433 and not 5432?**
There was already a native PostgreSQL installation running on this machine using port 5432.
Mapping Docker to 5433 avoids the conflict — see [Section 15](#15-port-conflict-fix-explained) for the full story.

**Commands used:**
```bash
docker compose up -d       # Start in the background (-d = detached)
docker compose ps          # Check it is running
```

**Result:** A live PostgreSQL server is running, accessible at `localhost:5433`, with an empty database called `taskmanager`.

---

## 3. Step 2 — Connecting Python to the Database

**File:** `backend/app/database.py`

SQLAlchemy is the ORM (Object Relational Mapper). It lets you write Python instead of SQL. This file sets up the engine (the connection) and the session factory (how you get a connection to use in a request).

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

engine = create_engine(
    settings.DATABASE_URL,   # "postgresql://postgres:password@localhost:5433/taskmanager"
    pool_pre_ping=True,      # Tests the connection is alive before using it
    pool_size=10,            # Keep up to 10 open connections ready
    max_overflow=20,         # Allow 20 more when all 10 are busy
)

SessionLocal = sessionmaker(
    autocommit=False,        # Never commit automatically — we do it explicitly
    autoflush=False,         # Don't write to DB until we call commit()
    bind=engine,
)

Base = declarative_base()   # All ORM models will inherit from this
```

**In plain English:**
- `engine` = the phone line to the database
- `SessionLocal` = a factory that hands out individual phone calls (one per request)
- `Base` = the shared blueprint that all table classes are built from

---

## 4. Step 3 — Reading Config from the .env File

**File:** `backend/app/config.py`  
**Secret values:** `backend/.env`

Hard-coding passwords and secret keys in code is a security risk. Instead, they live in a `.env` file which is never committed to git.

**The `.env` file:**
```
DATABASE_URL=postgresql://postgres:password@localhost:5433/taskmanager
SECRET_KEY=supersecretkey1234567890abcdefghijklmno
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

**`config.py` reads it using Pydantic Settings:**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"

settings = Settings()   # One shared instance used across the whole app
```

**How it works:**  
When `Settings()` is created, Pydantic automatically reads the `.env` file and maps each variable to the corresponding field. If a required variable is missing, it raises an error immediately at startup — so you catch configuration mistakes before any user request hits the app.

**Usage anywhere in the app:**
```python
from app.config import settings

print(settings.DATABASE_URL)            # postgresql://postgres:password@...
print(settings.ACCESS_TOKEN_EXPIRE_MINUTES)  # 60
```

---

## 5. Step 4 — ORM Models (Database Tables as Python Classes)

**Files:** `backend/app/models/user.py` and `backend/app/models/task.py`

An ORM model is a Python class where each attribute maps to a column in a database table. SQLAlchemy reads these classes and knows how to generate the correct SQL.

### User model

```python
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from ..database import Base

class User(Base):
    __tablename__ = "users"

    id             = Column(Integer, primary_key=True, index=True)
    email          = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
```

**What this creates in PostgreSQL:**
```sql
CREATE TABLE users (
    id               SERIAL PRIMARY KEY,
    email            VARCHAR UNIQUE NOT NULL,
    hashed_password  VARCHAR NOT NULL,
    created_at       TIMESTAMPTZ DEFAULT now()
);
```

Notice `hashed_password` — the plain-text password is **never stored**. Only the bcrypt hash.

### Task model

```python
class Task(Base):
    __tablename__ = "tasks"

    id           = Column(Integer, primary_key=True, index=True)
    title        = Column(String, nullable=False)
    description  = Column(String, nullable=True)
    priority     = Column(String, default="medium")   # "low", "medium", "high"
    status       = Column(String, default="pending")  # "pending", "completed"
    due_date     = Column(DateTime(timezone=True), nullable=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    owner_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
```

`owner_id` is a **foreign key** — it links every task back to the user who created it. This is how we ensure users can only see and edit their own tasks.

---

## 6. Step 5 — Alembic Migrations (Creating the Tables)

**Tool:** Alembic  
**Files:** `backend/alembic/` and `backend/alembic.ini`

The ORM models define *what* the tables should look like. Alembic is the tool that actually *creates or changes* those tables in the running database. It keeps a history of every change so you can roll forward or backward.

**Step 1 — Generate a migration (Alembic reads the models and writes the SQL for you):**
```bash
alembic revision --autogenerate -m "create users and tasks tables"
```

Alembic compared the models to the empty database and generated this file automatically:

```python
# alembic/versions/f4e4ae5cab83_create_users_and_tasks_tables.py

def upgrade() -> None:
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        # ... all other columns ...
        sa.ForeignKeyConstraint(['owner_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('tasks')
    op.drop_table('users')
```

**Step 2 — Apply the migration:**
```bash
alembic upgrade head
```

**Result — verified inside the database:**
```
taskmanager=# \dt
              List of relations
 Schema |      Name       | Type  |  Owner
--------+-----------------+-------+----------
 public | alembic_version | table | postgres   ← tracks which migrations have run
 public | tasks           | table | postgres
 public | users           | table | postgres
```

---

## 7. Step 6 — Password Hashing and JWT Tokens

**File:** `backend/app/core/security.py`

This file handles two security concerns: storing passwords safely, and proving a user is logged in.

### Password hashing with bcrypt

Passwords are **never stored as plain text**. bcrypt turns "mysecret123" into a long scrambled hash. Even if someone stole the database, they could not recover the original password.

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

**Example:**
```python
hash = hash_password("mysecret123")
# hash = "$2b$12$eImiTXuWVxfM37uY4JANjQ..."  (different every time due to random salt)

verify_password("mysecret123", hash)   # True
verify_password("wrongpassword", hash) # False
```

### JWT tokens

After login, the server hands the user a **JWT (JSON Web Token)** — a digitally signed string that proves their identity. Every protected request must include this token.

```python
from jose import jwt, JWTError

def create_access_token(data: dict) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire})
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None  # Token is invalid or expired
```

**Example — what the token contains (before encoding):**
```python
payload = {"sub": "42", "exp": 1713600000}
# "sub" = user ID 42
# "exp" = expiry timestamp (60 minutes from now)
```

The token is signed with `SECRET_KEY`. Anyone can read the payload (it is base64 encoded, not encrypted), but they cannot **forge** a new one without the secret key.

---

## 8. Step 7 — Dependencies (get_db and get_current_user)

**File:** `backend/app/core/deps.py`

FastAPI has a dependency injection system. Instead of writing the same boilerplate in every route, you declare what a route *needs* and FastAPI provides it automatically.

### get_db — gives each request its own database session

```python
def get_db():
    db = SessionLocal()   # Open a new connection from the pool
    try:
        yield db          # Hand it to the route handler
    finally:
        db.close()        # Always close it, even if the route raised an exception
```

**How routes use it:**
```python
@router.get("/tasks/")
def list_tasks(db: Session = Depends(get_db)):
    # db is already open and ready — no setup needed here
    return db.query(Task).all()
```

### get_current_user — identifies who is making the request

```python
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def get_current_user(
    token: str = Depends(oauth2_scheme),  # Reads the Bearer token from the header
    db: Session = Depends(get_db),
) -> User:
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    user_id = payload.get("sub")          # Extract the user ID stored in the token
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    return user
```

**How routes use it:**
```python
@router.get("/tasks/")
def list_tasks(current_user: User = Depends(get_current_user)):
    # current_user is the full User object — no manual token parsing needed
    print(current_user.email)   # "alice@example.com"
```

Any route that uses `Depends(get_current_user)` is automatically **protected** — unauthenticated requests get a 401 response before the route body even runs.

---

## 9. Step 8 — Pydantic Schemas (Validating Request and Response Data)

**Files:** `backend/app/schemas/user.py` and `backend/app/schemas/task.py`

Schemas are the "contracts" for data entering and leaving the API. Pydantic validates every field automatically — wrong types or missing required fields return a clear 422 error before your code runs.

### User schemas

```python
class UserCreate(BaseModel):
    email: EmailStr   # Must be a valid email format — e.g. "alice@example.com"
    password: str     # Required plain-text password (only used to create a hash)

class UserOut(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime
    model_config = {"from_attributes": True}  # Allows reading from SQLAlchemy objects

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
```

**Why `UserOut` does not include `hashed_password`:**  
The schema controls exactly what gets serialised into the JSON response. Since `hashed_password` is not listed in `UserOut`, it is **never sent back to the client** — even though it exists on the database model.

### Task schemas

```python
class TaskCreate(BaseModel):
    title: str                         # Required
    description: Optional[str] = None # Optional
    priority: Optional[str] = "medium"
    status: Optional[str] = "pending"
    due_date: Optional[datetime] = None

class TaskUpdate(BaseModel):
    # Every field is Optional — PATCH only updates what you send
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    priority: str
    status: str
    due_date: Optional[datetime]
    created_at: datetime
    completed_at: Optional[datetime]
    owner_id: int
    model_config = {"from_attributes": True}
```

**Example — creating a task:**

Request body sent by the client:
```json
{
  "title": "Write unit tests",
  "priority": "high",
  "due_date": "2026-04-25T09:00:00Z"
}
```
Pydantic validates this against `TaskCreate`. `description` and `status` get their defaults. The response is serialised through `TaskOut`.

---

## 10. Step 9 — Auth Routes (Register, Login, Me)

**File:** `backend/app/routers/auth.py`

### POST /auth/register

Creates a new user account.

```python
@router.post("/register", response_model=UserOut, status_code=201)
def register(body: UserCreate, db: Session = Depends(get_db)):
    # 1. Check the email is not already taken
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2. Hash the password — never store plain text
    user = User(email=body.email, hashed_password=hash_password(body.password))

    # 3. Save to database
    db.add(user)
    db.commit()
    db.refresh(user)   # Reload from DB so id and created_at are populated
    return user
```

**Request:**
```
POST /auth/register
Content-Type: application/json

{ "email": "alice@example.com", "password": "securepass123" }
```

**Response (201 Created):**
```json
{ "id": 1, "email": "alice@example.com", "created_at": "2026-04-18T10:00:00Z" }
```

Note: `password` is accepted but `hashed_password` is never returned.

---

### POST /auth/token

Logs in and returns a JWT. Uses the OAuth2 form format (username + password fields) because that is what the Swagger UI's Authorize button expects.

```python
@router.post("/token", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form.username).first()

    # Fail if user not found OR if password does not match the stored hash
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    # Create a token with the user's ID embedded inside
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}
```

**Request:**
```
POST /auth/token
Content-Type: application/x-www-form-urlencoded

username=alice@example.com&password=securepass123
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

From this point on, the client must send this token in every request:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

### GET /auth/me

Returns the currently logged-in user. Protected — requires a valid token.

```python
@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user   # get_current_user already did all the token work
```

**Response:**
```json
{ "id": 1, "email": "alice@example.com", "created_at": "2026-04-18T10:00:00Z" }
```

---

## 11. Step 10 — Task Routes (Full CRUD + Stats)

**File:** `backend/app/routers/tasks.py`

Every route filters by `owner_id == current_user.id`. This means a user can **only ever see or modify their own tasks** — even if they guess another task's ID, they get a 404.

### GET /tasks/stats/summary

Returns a count breakdown for the dashboard.

```python
@router.get("/stats/summary")
def stats_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    base = db.query(Task).filter(Task.owner_id == current_user.id)
    now = datetime.now(timezone.utc)
    return {
        "total":     base.count(),
        "completed": base.filter(Task.status == "completed").count(),
        "pending":   base.filter(Task.status == "pending").count(),
        "overdue":   base.filter(Task.due_date < now, Task.status != "completed").count(),
    }
```

**Response:**
```json
{ "total": 10, "completed": 4, "pending": 5, "overdue": 1 }
```

---

### GET /tasks/ — List with optional filters

```python
@router.get("/", response_model=list[TaskOut])
def list_tasks(
    status: Optional[str] = Query(None),      # ?status=pending
    priority: Optional[str] = Query(None),    # ?priority=high
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Task).filter(Task.owner_id == current_user.id)
    if status:
        q = q.filter(Task.status == status)
    if priority:
        q = q.filter(Task.priority == priority)
    return q.order_by(Task.created_at.desc()).all()
```

**Examples:**
```
GET /tasks/                       → all your tasks
GET /tasks/?status=pending        → only pending tasks
GET /tasks/?priority=high         → only high priority tasks
GET /tasks/?status=pending&priority=high  → both filters applied
```

---

### POST /tasks/ — Create

```python
@router.post("/", response_model=TaskOut, status_code=201)
def create_task(body: TaskCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = Task(**body.model_dump(), owner_id=current_user.id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task
```

**Request:**
```json
{ "title": "Buy groceries", "priority": "low" }
```
**Response (201):**
```json
{
  "id": 7, "title": "Buy groceries", "description": null,
  "priority": "low", "status": "pending",
  "due_date": null, "created_at": "2026-04-18T14:00:00Z",
  "completed_at": null, "owner_id": 1
}
```

---

### GET /tasks/{task_id} — Get one

```python
@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id, Task.owner_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
```

If user A tries `GET /tasks/99` and task 99 belongs to user B → **404**, not 403. This hides the existence of other users' tasks entirely.

---

### PATCH /tasks/{task_id} — Update (partial)

```python
@router.patch("/{task_id}", response_model=TaskOut)
def update_task(task_id: int, body: TaskUpdate, ...):
    task = db.query(Task).filter(Task.id == task_id, Task.owner_id == current_user.id).first()

    updates = body.model_dump(exclude_unset=True)  # Only fields actually sent in the request

    # Smart auto-complete: if marking as completed, record the timestamp
    if updates.get("status") == "completed" and task.status != "completed":
        updates.setdefault("completed_at", datetime.now(timezone.utc))

    for field, value in updates.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task
```

**Example — mark a task complete:**
```json
PATCH /tasks/7
{ "status": "completed" }
```
`completed_at` is automatically set to the current time — you don't need to send it.

---

### DELETE /tasks/{task_id}

```python
@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id, Task.owner_id == current_user.id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    # 204 = success, no body returned
```

---

## 12. Step 11 — Wiring Everything Together in main.py

**File:** `backend/app/main.py`

This is the entry point. It creates the FastAPI application, adds CORS middleware so the React frontend can talk to it, and mounts both routers.

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, tasks

app = FastAPI(title="Task Manager API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)    # Mounts /auth/register, /auth/token, /auth/me
app.include_router(tasks.router)   # Mounts all /tasks/ endpoints

@app.get("/")
def root():
    return {"message": "Task Manager API is running"}
```

**CORS explained:**  
Browsers block JavaScript from calling an API on a different port (e.g. React on 5173 calling FastAPI on 8000) unless the API explicitly allows it. `CORSMiddleware` adds the response headers that tell the browser "this is allowed".

**All registered routes:**
```
GET  /
POST /auth/register
POST /auth/token
GET  /auth/me
GET  /tasks/stats/summary
GET  /tasks/
POST /tasks/
GET  /tasks/{task_id}
PATCH /tasks/{task_id}
DELETE /tasks/{task_id}
GET  /docs               ← Swagger UI (auto-generated, interactive)
GET  /redoc              ← ReDoc UI (alternative docs)
```

---

## 13. How a Real Request Flows Through the App

**Scenario:** Alice marks task #7 as completed.

```
PATCH /tasks/7
Authorization: Bearer eyJhbGc...
Content-Type: application/json

{ "status": "completed" }
```

**Step-by-step through the code:**

```
1. FastAPI receives the request
       ↓
2. CORSMiddleware checks the Origin header is allowed
       ↓
3. FastAPI matches the route → update_task() in routers/tasks.py
       ↓
4. Depends(get_current_user) is resolved:
     a. OAuth2PasswordBearer reads the "Authorization: Bearer ..." header
     b. decode_access_token() verifies the JWT signature and expiry
     c. Extracts sub = "1" (Alice's user ID)
     d. Queries DB: SELECT * FROM users WHERE id = 1
     e. Returns the User object for Alice
       ↓
5. Depends(get_db) is resolved:
     a. Opens a SQLAlchemy session from the pool
       ↓
6. Pydantic validates the request body { "status": "completed" } against TaskUpdate
       ↓
7. Route body runs:
     a. SELECT * FROM tasks WHERE id = 7 AND owner_id = 1
     b. Found — task belongs to Alice
     c. body.model_dump(exclude_unset=True) → {"status": "completed"}
     d. status is "completed" and was previously "pending" → auto-sets completed_at = now()
     e. task.status = "completed", task.completed_at = 2026-04-18T14:35:00Z
     f. db.commit() → UPDATE tasks SET status=..., completed_at=... WHERE id=7
       ↓
8. Updated task is serialised through TaskOut schema
       ↓
9. JSON response returned:

{
  "id": 7, "title": "Buy groceries",
  "status": "completed", "priority": "low",
  "completed_at": "2026-04-18T14:35:00Z",
  "created_at": "2026-04-18T14:00:00Z",
  "owner_id": 1, ...
}
       ↓
10. get_db finally block runs → session closed, connection returned to pool
```

---

## 14. How to Start the Backend

```bash
# Terminal 1 — start the database
docker compose up -d

# Terminal 2 — start the API server
cd backend
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux

uvicorn app.main:app --reload --port 8000
```

Then open `http://localhost:8000/docs` — you will see the full interactive Swagger UI.

**To test the full auth flow in Swagger:**
1. Use `POST /auth/register` to create an account
2. Use `POST /auth/token` with your email and password → copy the `access_token`
3. Click **Authorize** (top right), paste the token
4. Now all task endpoints will work as that logged-in user

---

## 15. Port Conflict Fix Explained

During setup, psycopg2 kept returning "password authentication failed" even though the credentials were correct. The root cause was a **port conflict**.

**Discovery:**
```
netstat -ano | grep :5432

TCP  0.0.0.0:5432  LISTENING  15804  ← Docker Desktop
TCP  0.0.0.0:5432  LISTENING  7692   ← native postgres.exe
```

Two processes were both listening on port 5432. When Python connected to `localhost:5432`, Windows was routing it to the **native PostgreSQL** (PID 7692) — which had a completely different password — instead of the Docker container.

**Fix:**  
Changed `docker-compose.yml` to map host port `5433` → container port `5432`:
```yaml
ports:
  - '5433:5432'   # was '5432:5432'
```

Updated `.env` to match:
```
DATABASE_URL=postgresql://postgres:password@localhost:5433/taskmanager
```

This completely avoids the conflict. The native PostgreSQL continues to run on 5432 undisturbed, and the Docker container is now reachable on 5433.
