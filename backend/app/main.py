# main.py — Entry point for the FastAPI application.
# This is the first file Uvicorn loads when you run:
#   uvicorn app.main:app --reload --port 8000
# It creates the app instance, registers middleware, and mounts all routers.

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, tasks

# Create the FastAPI application instance.
# The title appears in the auto-generated Swagger UI at /docs.
app = FastAPI(title="Taska API")

# --- CORS Middleware ---
# CORS (Cross-Origin Resource Sharing) is a browser security rule.
# By default, a browser will BLOCK JavaScript running on one origin (e.g. localhost:5173)
# from making requests to a different origin (e.g. localhost:8000).
# This middleware adds the correct response headers to tell the browser:
# "requests from localhost:5173 are allowed — let them through."
origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")]
print("CORS allowed origins:", origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    return {"message": "Taska API is running"}
