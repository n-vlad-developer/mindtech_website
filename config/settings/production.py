from .base import *
import os

# --- helpers (на случай если в base.py нет env/env_bool) ---
def _env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)

def _env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")

def _env_int(name: str, default: int = 0) -> int:
    v = os.getenv(name)
    try:
        return int(v) if v is not None else default
    except ValueError:
        return default

def _env_csv(name: str) -> list[str]:
    v = os.getenv(name, "")
    return [x.strip() for x in v.split(",") if x.strip()]

# если в base.py есть env/env_bool — используем их, иначе наши
env = globals().get("env", _env)
env_bool = globals().get("env_bool", _env_bool)

DEBUG = env_bool("DEBUG", False)

# секрет и хосты/CSRF из env (рекомендуется)
SECRET_KEY = os.getenv("SECRET_KEY", SECRET_KEY)

ALLOWED_HOSTS = _env_csv("ALLOWED_HOSTS") or ALLOWED_HOSTS

CSRF_TRUSTED_ORIGINS = _env_csv("CSRF_TRUSTED_ORIGINS") or []

WAGTAILADMIN_BASE_URL = os.getenv("WAGTAILADMIN_BASE_URL", WAGTAILADMIN_BASE_URL)

# статика: whitenoise (как ты хотел)
STORAGES["staticfiles"]["BACKEND"] = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# --- IIS reverse proxy / HTTPS ---
# IIS должен отдавать заголовок X-Forwarded-Proto=https (мы это в web.config ставили)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

# безопасность (можно управлять env'ом)
# если редирект на https уже делает IIS, держи SECURE_SSL_REDIRECT=0 в .env
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", False)

SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", True)
CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", True)

SECURE_HSTS_SECONDS = _env_int("SECURE_HSTS_SECONDS", 0)  # поставишь 31536000 когда https точно ок
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", False)
SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", False)


# язык/таймзона (если задаёшь в .env)
TIME_ZONE = os.getenv("TIME_ZONE", TIME_ZONE)
LANGUAGE_CODE = os.getenv("LANGUAGE_CODE", LANGUAGE_CODE)

try:
    from .local import *
except ImportError:
    pass
