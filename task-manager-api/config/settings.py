import os
from pathlib import Path

try:
    from dotenv import load_dotenv

    env_file = Path(__file__).resolve().parent.parent / ".env"
    if env_file.exists():
        try:
            load_dotenv(dotenv_path=env_file, encoding="utf-8")
        except UnicodeDecodeError:
            # Ignora .env com encoding inválido; usa os.environ / defaults.
            pass
except ImportError:
    pass


def _bool(value, default=False):
    if value is None:
        return default
    return str(value).lower() in ("1", "true", "yes", "on")


SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
DEBUG = _bool(os.environ.get("DEBUG"), default=False)
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "5000"))
SQLALCHEMY_DATABASE_URI = os.environ.get(
    "SQLALCHEMY_DATABASE_URI", "sqlite:///tasks.db"
)
SQLALCHEMY_TRACK_MODIFICATIONS = False

SMTP_HOST = os.environ.get("SMTP_HOST", "localhost")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SMTP_ENABLED = _bool(os.environ.get("SMTP_ENABLED"), default=False)

TOKEN_MAX_AGE_SECONDS = int(os.environ.get("TOKEN_MAX_AGE_SECONDS", "86400"))
