# main.py — Entry point for the FastAPI application.
# This is the first file Uvicorn loads when you run:
#   uvicorn app.main:app --reload --port 8000
# It creates the app instance, registers middleware, and mounts all routers.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, tasks

# Create the FastAPI application instance.
# The title appears in the auto-generated Swagger UI at /docs.
app = FastAPI(title="Task Manager API")

# --- CORS Middleware ---
# CORS (Cross-Origin Resource Sharing) is a browser security rule.
# By default, a browser will BLOCK JavaScript running on one origin (e.g. localhost:5173)
# from making requests to a different origin (e.g. localhost:8000).
# This middleware adds the correct response headers to tell the browser:
# "requests from localhost:5173 are allowed — let them through."
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server (React frontend)
    allow_credentials=True,                   # Allow cookies and Authorization headers
    allow_methods=["*"],                      # Allow all HTTP methods: GET, POST, PATCH, DELETE, etc.
    allow_headers=["*"],                      # Allow all headers including Authorization
)

# --- Routers ---
# Routers are groups of related routes defined in separate files.
# include_router() mounts them onto the main app.
# auth.router adds:  POST /auth/register, POST /auth/token, GET /auth/me
# tasks.router adds: GET/POST /tasks/, GET/PATCH/DELETE /tasks/{id}, GET /tasks/stats/summary
app.include_router(auth.router)
app.include_router(tasks.router)


# --- Health check route ---
# A simple root endpoint used to verify the server is running.
# Visit http://localhost:8000/ to confirm the API is alive.
@app.get("/")
def root():
    return {"message": "Task Manager API is running"}
