# Taska — Full Build Log

A detailed, step-by-step explanation of everything built, with real examples from the actual code.

---

## Table of Contents

### Backend (Phase 1 & 2)
1. [Project Structure](#1-project-structure)
2. [Database with Docker Compose](#2-database-with-docker-compose)
3. [Connecting Python to the Database](#3-connecting-python-to-the-database)
4. [Reading Config from .env](#4-reading-config-from-env)
5. [ORM Models](#5-orm-models)
6. [Alembic Migrations](#6-alembic-migrations)
7. [Password Hashing and JWT Tokens](#7-password-hashing-and-jwt-tokens)
8. [Dependencies — get_db and get_current_user](#8-dependencies)
9. [Pydantic Schemas](#9-pydantic-schemas)
10. [Auth Routes](#10-auth-routes)
11. [Task Routes](#11-task-routes)
12. [Wiring Everything Together](#12-wiring-everything-together)
13. [How a Request Flows Through the App](#13-how-a-request-flows)
14. [How to Start the Backend](#14-how-to-start-the-backend)
15. [Port Conflict Fix](#15-port-conflict-fix)

### Frontend (Phase 3)
16. [Frontend Setup](#16-frontend-setup)
17. [Project Structure](#17-frontend-project-structure)
18. [TypeScript Types](#18-typescript-types)
19. [API Client](#19-api-client)
20. [Auth Context](#20-auth-context)
21. [Routing and Route Guards](#21-routing-and-route-guards)
22. [Login and Register Pages](#22-login-and-register-pages)
23. [Dashboard Page](#23-dashboard-page)
24. [Task Card Component](#24-task-card-component)
25. [Task Modal](#25-task-modal)
26. [Theme System](#26-theme-system)
27. [Settings Page](#27-settings-page)
28. [Toast Notifications](#28-toast-notifications)
29. [Pre-ship Polish](#29-pre-ship-polish)

---

## 1. Project Structure

```
task-manager/
├── docker-compose.yml
├── backend/
│   ├── .env
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/versions/
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── database.py
│       ├── models/user.py
│       ├── models/task.py
│       ├── schemas/user.py
│       ├── schemas/task.py
│       ├── core/security.py
│       ├── core/deps.py
│       ├── routers/auth.py
│       └── routers/tasks.py
└── frontend/
    └── src/
        ├── api/client.ts
        ├── api/auth.ts
        ├── api/tasks.ts
        ├── hooks/useAuth.tsx
        ├── hooks/useTheme.tsx
        ├── hooks/useToast.tsx
        ├── components/TaskCard.tsx
        ├── components/TaskModal.tsx
        ├── components/ToastContainer.tsx
        ├── pages/LoginPage.tsx
        ├── pages/RegisterPage.tsx
        ├── pages/DashboardPage.tsx
        ├── pages/SettingsPage.tsx
        └── types/index.ts
```

---

## 2. Database with Docker Compose

**File:** `docker-compose.yml`

Instead of installing PostgreSQL directly, Docker runs it in a container.

```yaml
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: taskmanager
    ports:
      - '5433:5432'   # host 5433 → container 5432 (avoids conflict with local postgres)
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

```bash
docker compose up -d    # start in background
docker compose ps       # verify it's running
```

---

## 3. Connecting Python to the Database

**File:** `backend/app/database.py`

SQLAlchemy is the ORM. This file creates the engine (the connection) and a session factory.

```python
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,   # test connection before using it
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()   # all models inherit from this
```

- `engine` = the connection to the database
- `SessionLocal` = factory that gives each request its own session
- `Base` = shared blueprint for all table classes

---

## 4. Reading Config from .env

**Files:** `backend/app/config.py` and `backend/.env`

Passwords and secret keys live in `.env`, never in code.

```
DATABASE_URL=postgresql://postgres:password@localhost:5433/taskmanager
SECRET_KEY=supersecretkey1234567890abcdefghijklmno
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

```python
class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"

settings = Settings()
```

Pydantic reads the `.env` file automatically. If a required variable is missing it raises an error at startup before any request reaches the app.

---

## 5. ORM Models

**Files:** `backend/app/models/user.py` and `backend/app/models/task.py`

Each class maps to a database table.

```python
class User(Base):
    __tablename__ = "users"
    id              = Column(Integer, primary_key=True, index=True)
    email           = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
```

```python
class Task(Base):
    __tablename__ = "tasks"
    id           = Column(Integer, primary_key=True, index=True)
    title        = Column(String, nullable=False)
    description  = Column(String, nullable=True)
    priority     = Column(String, default="medium")   # low / medium / high
    status       = Column(String, default="pending")  # pending / completed
    due_date     = Column(DateTime(timezone=True), nullable=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    owner_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
```

`owner_id` is a foreign key — every task is linked to the user who created it.

---

## 6. Alembic Migrations

Alembic creates and tracks schema changes in the real database.

```bash
# Generate migration from the models
alembic revision --autogenerate -m "create users and tasks tables"

# Apply it
alembic upgrade head
```

Alembic generates a Python file with `upgrade()` and `downgrade()` functions. Running `upgrade head` applies all pending migrations. The `alembic_version` table tracks which ones have run.

---

## 7. Password Hashing and JWT Tokens

**File:** `backend/app/core/security.py`

**Passwords** are hashed with bcrypt — never stored as plain text.

```python
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

**JWT tokens** are issued after login. They contain the user's ID and an expiry timestamp, signed with the `SECRET_KEY`.

```python
def create_access_token(data: dict) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire})
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
```

The token is base64-encoded (readable), but can only be forged with the secret key — so it's tamper-proof.

---

## 8. Dependencies

**File:** `backend/app/core/deps.py`

FastAPI's dependency injection system lets you declare what a route needs. FastAPI provides it automatically.

```python
def get_db():
    db = SessionLocal()
    try:
        yield db        # hand the session to the route
    finally:
        db.close()      # always close it, even on error
```

```python
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    return user
```

Any route that declares `Depends(get_current_user)` is automatically protected.

---

## 9. Pydantic Schemas

**Files:** `backend/app/schemas/user.py` and `backend/app/schemas/task.py`

Schemas define what data the API accepts and returns. They are separate from the ORM models.

```python
class UserCreate(BaseModel):
    email: EmailStr
    password: str

    @field_validator('password')
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class UserOut(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime
    model_config = {"from_attributes": True}
```

`UserOut` does not include `hashed_password` — Pydantic only serialises fields listed in the schema, so the hash is never sent to the client.

---

## 10. Auth Routes

**File:** `backend/app/routers/auth.py`

| Method | Path | What it does |
|--------|------|-------------|
| POST | /auth/register | Create account, returns user |
| POST | /auth/token | Login, returns JWT |
| GET | /auth/me | Return current user (protected) |
| PATCH | /auth/password | Change password (protected) |

Key pattern in register: check for duplicate email → hash password → save → return user through `UserOut` (no hash exposed).

Key pattern in login: look up user by email → verify password → create JWT with `{"sub": str(user.id)}` → return token.

---

## 11. Task Routes

**File:** `backend/app/routers/tasks.py`

Every route filters by `owner_id == current_user.id`. A user can only ever see their own tasks.

| Method | Path | What it does |
|--------|------|-------------|
| GET | /tasks/stats/summary | Counts: total, pending, completed, overdue |
| GET | /tasks/ | List tasks (optional ?status= and ?priority= filters) |
| POST | /tasks/ | Create a task |
| GET | /tasks/{id} | Get one task |
| PATCH | /tasks/{id} | Partial update |
| DELETE | /tasks/{id} | Delete |

The PATCH endpoint uses `model_dump(exclude_unset=True)` so only fields actually sent in the request body are updated. If status is changed to "completed", `completed_at` is auto-set.

---

## 12. Wiring Everything Together

**File:** `backend/app/main.py`

```python
app = FastAPI(title="Taska API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(tasks.router)
```

CORS is required because the browser blocks JavaScript on port 5173 from calling an API on port 8000 unless the API explicitly allows it.

---

## 13. How a Request Flows

**Scenario:** Alice marks task #7 as completed.

```
PATCH /tasks/7  { "status": "completed" }
Authorization: Bearer eyJhbGc...

1. CORS middleware checks the origin is allowed
2. FastAPI matches the route → update_task()
3. Depends(get_current_user):
   - reads Bearer token from header
   - verifies JWT signature and expiry
   - extracts sub = "1" (Alice's user ID)
   - queries DB for User with id=1
4. Depends(get_db): opens a session
5. Pydantic validates { "status": "completed" } against TaskUpdate
6. Route body runs:
   - SELECT task WHERE id=7 AND owner_id=1
   - model_dump(exclude_unset=True) → {"status": "completed"}
   - auto-sets completed_at = now()
   - db.commit()
7. Response serialised through TaskOut schema
8. Session closed, connection returned to pool
```

---

## 14. How to Start the Backend

```bash
docker compose up -d

cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

Open `http://localhost:8000/docs` for the interactive Swagger UI.

---

## 15. Port Conflict Fix

During setup, psycopg2 returned "password authentication failed" even though credentials were correct. The cause was two processes both listening on port 5432 — Docker and a native PostgreSQL installation. Windows routed connections to the wrong one.

**Fix:** Map Docker to host port 5433 instead:
```yaml
ports:
  - '5433:5432'
```

Update `DATABASE_URL` in `.env` to use port 5433.

---

## 16. Frontend Setup

**Stack:** Vite + React 19 + TypeScript + Tailwind CSS v4

```bash
npm create vite@latest . -- --template react-ts
npm install
npm install axios react-router-dom
npm install -D tailwindcss @tailwindcss/vite
```

**`vite.config.ts`** — add the Tailwind plugin:
```ts
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
})
```

**`src/index.css`** — Tailwind v4 uses CSS-first config:
```css
@import "tailwindcss";
@variant dark (&:where(.dark, .dark *));
```

The `@variant dark` line tells Tailwind that `dark:` utility classes apply when any ancestor element has the class `dark`. This enables class-based dark mode (as opposed to the default `prefers-color-scheme` media query).

---

## 17. Frontend Project Structure

```
src/
├── api/
│   ├── client.ts      # axios instance — attaches token, handles 401
│   ├── auth.ts        # register, login, getMe, changePassword
│   └── tasks.ts       # CRUD + stats
├── hooks/
│   ├── useAuth.tsx    # auth context — user, token, logout
│   ├── useTheme.tsx   # theme context — light/dark/system
│   └── useToast.tsx   # toast context — success/error notifications
├── components/
│   ├── TaskCard.tsx       # single task row with toggle/edit/delete
│   ├── TaskModal.tsx      # create/edit modal
│   └── ToastContainer.tsx # renders the toast stack
├── pages/
│   ├── LoginPage.tsx
│   ├── RegisterPage.tsx
│   ├── DashboardPage.tsx
│   └── SettingsPage.tsx
└── types/index.ts     # shared TypeScript interfaces
```

---

## 18. TypeScript Types

**File:** `src/types/index.ts`

Shared interfaces that match the backend's Pydantic schemas exactly. Defining them once means TypeScript catches mismatches everywhere automatically.

```ts
export interface Task {
  id: number
  title: string
  description: string | null
  priority: 'low' | 'medium' | 'high'
  status: 'pending' | 'completed'
  due_date: string | null
  created_at: string
  completed_at: string | null
  owner_id: number
}
```

Using string literal unions (`'low' | 'medium' | 'high'`) instead of plain `string` means TypeScript will error if you pass an invalid priority anywhere in the app.

---

## 19. API Client

**File:** `src/api/client.ts`

A single Axios instance shared by all API calls. Two interceptors do the heavy lifting:

```ts
const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000',
})

// Request interceptor — attach JWT to every request automatically
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// Response interceptor — on 401, clear token and redirect to login
client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      sessionStorage.setItem('session_expired', '1')  // login page reads this
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)
```

`VITE_API_URL` comes from `frontend/.env`. In production you change this one variable and the whole app points to the production server.

---

## 20. Auth Context

**File:** `src/hooks/useAuth.tsx`

A React context that holds the current user and token. Wraps the whole app so any component can access auth state.

```tsx
export function AuthProvider({ children }) {
  const [token, setTokenState] = useState(localStorage.getItem('token'))
  const [user, setUser] = useState(null)

  useEffect(() => {
    if (!token) return
    getMe().then(setUser).catch(() => setToken(null))
  }, [token])

  // ...
}

export const useAuth = () => useContext(AuthContext)
```

On mount, if a token exists in `localStorage`, it calls `GET /auth/me` to verify it's still valid and fetch the user's details. If the token is expired or invalid, it clears it.

---

## 21. Routing and Route Guards

**File:** `src/App.tsx`

Two guard components control access:

```tsx
function ProtectedRoute({ children }) {
  const { token, loading } = useAuth()
  if (loading) return <LoadingSpinner />
  return token ? <>{children}</> : <Navigate to="/login" replace />
}

function GuestRoute({ children }) {
  const { token, loading } = useAuth()
  if (loading) return null
  return !token ? <>{children}</> : <Navigate to="/" replace />
}
```

`ProtectedRoute` — redirects to `/login` if not logged in.
`GuestRoute` — redirects to `/` if already logged in (so you can't visit login while logged in).

The `loading` check is critical — without it, there's a flash where the app redirects before `getMe()` has finished, logging the user out momentarily.

---

## 22. Login and Register Pages

**Files:** `src/pages/LoginPage.tsx` and `src/pages/RegisterPage.tsx`

Login flow:
1. Submit email + password
2. Call `POST /auth/token` (form-encoded — OAuth2 standard)
3. Store token in `localStorage` via `setToken()`
4. React Router navigates to `/`

Register flow:
1. Validate passwords match and meet 8-character minimum (client-side, before hitting the server)
2. Call `POST /auth/register`
3. Immediately call `POST /auth/token` to log in
4. Store token and navigate to `/`

Session expiry banner — when the axios interceptor redirects to login after a 401, it sets `sessionStorage.setItem('session_expired', '1')`. LoginPage reads this on mount, shows a yellow banner, then clears the flag.

---

## 23. Dashboard Page

**File:** `src/pages/DashboardPage.tsx`

The main page. Fetches tasks and stats in parallel on load and after every action.

```ts
const [tasks, stats] = await Promise.all([getTasks(params), getStats()])
```

**Search** is applied client-side using `useMemo` — no extra API calls:
```ts
const displayedTasks = useMemo(() => {
  const q = search.trim().toLowerCase()
  const filtered = q
    ? tasks.filter(t => t.title.toLowerCase().includes(q) || t.description?.toLowerCase().includes(q))
    : tasks
  return sortTasks(filtered, sort)
}, [tasks, search, sort])
```

**Sort** options: newest first, oldest first, due date (nulls last), priority (high → medium → low).

**Filters** (status and priority) are sent as query params to the API — the backend handles them.

---

## 24. Task Card Component

**File:** `src/components/TaskCard.tsx`

Manages its own local state for two UX patterns:

**Loading on toggle** — the circular checkbox shows a spinner while the API call is in flight. The button is disabled to prevent double-clicks.

**Confirm before delete** — clicking the trash icon switches the card into a confirmation state showing "Delete? / Cancel / Delete" inline. No modal needed.

```tsx
const [confirming, setConfirming] = useState(false)
const [toggling, setToggling] = useState(false)
const [deleting, setDeleting] = useState(false)
```

The `onToggle` and `onDelete` props are async functions passed from `DashboardPage`. The card sets its own loading state around these calls, so only the specific card being interacted with shows a loading state — not the entire list.

---

## 25. Task Modal

**File:** `src/components/TaskModal.tsx`

Used for both create and edit. The parent passes an optional `task` prop — if it's provided, the form pre-fills with the task's current values.

Closes on:
- Clicking the Cancel button
- Pressing Escape (keyboard listener added in `useEffect`, cleaned up on unmount)
- Clicking the backdrop (the dark overlay behind the modal)

```tsx
useEffect(() => {
  const onKey = (e) => { if (e.key === 'Escape') onClose() }
  window.addEventListener('keydown', onKey)
  return () => window.removeEventListener('keydown', onKey)
}, [onClose])
```

---

## 26. Theme System

**File:** `src/hooks/useTheme.tsx`

Three modes: `light`, `dark`, `system`.

```tsx
function applyTheme(resolved: 'light' | 'dark') {
  document.documentElement.classList.toggle('dark', resolved === 'dark')
}
```

`system` mode listens for OS-level theme changes via `window.matchMedia`:

```tsx
const mq = window.matchMedia('(prefers-color-scheme: dark)')
mq.addEventListener('change', handler)
```

Choice is saved to `localStorage` and restored on the next visit. The `dark` class on `<html>` is applied synchronously during the initial render (not in a `useEffect`) to avoid a flash of the wrong theme on load.

Tailwind's `dark:` utilities are activated by the `@variant dark (&:where(.dark, .dark *))` line in `index.css` — any element that is a descendant of `.dark` gets the dark styles.

---

## 27. Settings Page

**File:** `src/pages/SettingsPage.tsx`

Two sections:

**Appearance** — three buttons (Light / Dark / System). The selected one gets an indigo border and background. Clicking one calls `setTheme()` from `useTheme`, which updates `localStorage`, `document.documentElement.classList`, and React state simultaneously.

**Change password** — three fields: current password, new password, confirm. Client-side checks:
- New passwords must match
- Minimum 8 characters

Then calls `PATCH /auth/password`. The backend verifies the current password against the stored hash before updating.

---

## 28. Toast Notifications

**Files:** `src/hooks/useToast.tsx` and `src/components/ToastContainer.tsx`

A simple pub/sub system using React context.

```tsx
const add = useCallback((message: string, type: Toast['type']) => {
  const id = ++nextId
  setToasts((prev) => [...prev, { id, message, type }])
  setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 3500)
}, [])
```

Each toast auto-dismisses after 3.5 seconds. It can also be manually dismissed by clicking the × button. Multiple toasts stack vertically in the bottom-right corner.

Used in `DashboardPage` after create, edit, and delete actions:
```ts
toast.success('Task created')
toast.success('Task deleted')
```

---

## 29. Pre-ship Polish

These are the fixes added before the app was considered ready to ship:

**Confirm before delete** — tasks used to delete instantly. Now there's an inline "Delete? / Cancel / Confirm" state on the card.

**Loading states** — the toggle button shows a spinner while the API call is in flight so there's visual feedback for every action.

**Environment variable for API URL** — `http://localhost:8000` was hardcoded. Moved to `frontend/.env` as `VITE_API_URL` so deployment only requires changing one variable.

**Password minimum length** — enforced on both client (Register page + Settings) and server (Pydantic `field_validator`).

**Token expiry banner** — when a 401 kicks you back to login, a yellow banner explains why instead of silently dropping you on the login page.

**Dependency fixes:**
- `pydantic[email]` — needed for `EmailStr` validation
- `bcrypt<4.0` — passlib is incompatible with bcrypt 4.x
