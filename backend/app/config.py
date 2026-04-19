# config.py — Application configuration using Pydantic Settings.
# Pydantic Settings reads environment variables from the .env file and maps
# them to typed Python attributes. If a required variable is missing or has
# the wrong type, the app crashes at startup with a clear error — so you
# catch configuration mistakes before any user request hits the server.
#
# The .env file lives at backend/.env and must NEVER be committed to git.
# Add it to .gitignore to keep secrets out of version control.

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Database ---
    # Full PostgreSQL connection string.
    # Format: postgresql://user:password@host:port/database_name
    # Example: postgresql://postgres:password@localhost:5433/taskmanager
    DATABASE_URL: str

    # --- JWT (JSON Web Token) ---
    # SECRET_KEY is used to sign tokens. Anyone with this key can forge tokens,
    # so keep it long, random, and private. Change it before going to production.
    SECRET_KEY: str

    # ALGORITHM tells python-jose which signing algorithm to use.
    # HS256 (HMAC + SHA-256) is a symmetric algorithm — the same key signs and verifies.
    ALGORITHM: str = "HS256"

    # How many minutes a token stays valid after it is issued.
    # After expiry the user must log in again to get a new token.
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        # Tell Pydantic where to find the .env file.
        # The path is relative to wherever the process is started from (the backend/ folder).
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Silently ignore any extra variables in .env that are not declared above.
        extra = "ignore"


# Create one shared Settings instance that is imported across the whole app.
# Usage in any file:
#   from app.config import settings
#   print(settings.DATABASE_URL)
settings = Settings()
