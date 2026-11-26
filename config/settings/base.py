from pathlib import Path
import os


PROJECT_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = PROJECT_DIR.parent


# ============================================================
# .env
# ============================================================

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

if load_dotenv:
    load_dotenv(BASE_DIR / ".env")


def env(name: str, default=None):
    return os.getenv(name, default)


def env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)

    if v is None:
        return default

    return v.strip().lower() in (
        "1",
        "true",
        "yes",
        "y",
        "on",
    )


def env_list(name: str, default=None):
    v = os.getenv(name)

    if not v:
        return default or []

    return [
        x.strip()
        for x in v.split(",")
        if x.strip()
    ]


# ============================================================
# CORE
# ============================================================

DEBUG = env_bool(
    "DEBUG",
    False,
)

SECRET_KEY = env(
    "SECRET_KEY",
    "django-insecure-change-me",
)

ALLOWED_HOSTS = env_list(
    "ALLOWED_HOSTS",
    [
        "127.0.0.1",
        "localhost",
    ],
)

CSRF_TRUSTED_ORIGINS = env_list(
    "CSRF_TRUSTED_ORIGINS",
    [
        "https://mindtech.kz",
        "https://www.mindtech.kz",
    ],
)


# ============================================================
# APPLICATIONS
# ============================================================

INSTALLED_APPS = [
    # django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",

    # PostgreSQL search
    "django.contrib.postgres",

    # Wagtail dependencies
    "taggit",
    "modelcluster",

    # Wagtail
    "wagtail",
    "wagtail.admin",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.sites",
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    "wagtail.contrib.settings",
    "wagtail.contrib.sitemaps",
    "wagtail.embeds",
    "wagtail.locales",

    # Wagtail Localize
    "wagtail_localize",

    # Project apps
    "home",
    "search",
]


# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",

    # обязательно перед CommonMiddleware
    "django.middleware.locale.LocaleMiddleware",

    "django.middleware.common.CommonMiddleware",

    "django.middleware.csrf.CsrfViewMiddleware",

    "django.contrib.auth.middleware.AuthenticationMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",

    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
]


# ============================================================
# URLS / WSGI
# ============================================================

ROOT_URLCONF = "config.urls"

WSGI_APPLICATION = "config.wsgi.application"


# ============================================================
# TEMPLATES
# ============================================================

TEMPLATES = [
    {
        "BACKEND": (
            "django.template.backends.django."
            "DjangoTemplates"
        ),

        "DIRS": [
            PROJECT_DIR / "templates",
        ],

        "APP_DIRS": True,

        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",

                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",

                "wagtail.contrib.settings.context_processors.settings",

                "home.context_processors.global_nav",
            ],
        },
    },
]


# ============================================================
# DATABASE
# ============================================================

DATABASES = {
    "default": {
        "ENGINE": (
            "django.db.backends.postgresql"
        ),

        "NAME": env(
            "DB_NAME",
            "mindtech_db",
        ),

        "USER": env(
            "DB_USER",
            "mindtech_user",
        ),

        "PASSWORD": env(
            "DB_PASSWORD",
            "",
        ),

        "HOST": env(
            "DB_HOST",
            "127.0.0.1",
        ),

        "PORT": env(
            "DB_PORT",
            "5432",
        ),
    }
}


# ============================================================
# PASSWORD VALIDATORS
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        )
    },

    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        )
    },

    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        )
    },

    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        )
    },
]


# ============================================================
# LANGUAGES / I18N
# ============================================================

WAGTAIL_I18N_ENABLED = True

LANGUAGES = [
    (
        "ru",
        "Русский",
    ),
    (
        "en",
        "English",
    ),
    (
        "kk",
        "Қазақша",
    ),
]

WAGTAIL_CONTENT_LANGUAGES = LANGUAGES

LANGUAGE_CODE = env(
    "LANGUAGE_CODE",
    "ru",
)

USE_I18N = True


# ============================================================
# TIMEZONE
# ============================================================

TIME_ZONE = env(
    "TIME_ZONE",
    "Asia/Almaty",
)

USE_TZ = True


# ============================================================
# STATIC FILES
# ============================================================

STATICFILES_FINDERS = [
    (
        "django.contrib.staticfiles.finders."
        "FileSystemFinder"
    ),

    (
        "django.contrib.staticfiles.finders."
        "AppDirectoriesFinder"
    ),
]

STATICFILES_DIRS = [
    PROJECT_DIR / "static",
]

STATIC_URL = "/static/"

STATIC_ROOT = (
    BASE_DIR
    / "staticfiles"
)


# ============================================================
# MEDIA
# ============================================================

MEDIA_URL = "/media/"

MEDIA_ROOT = (
    BASE_DIR
    / "media"
)


# ============================================================
# STORAGE
# ============================================================

STORAGES = {
    "default": {
        "BACKEND": (
            "django.core.files.storage."
            "FileSystemStorage"
        ),
    },

    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage."
            "StaticFilesStorage"
        ),
    },
}


# ============================================================
# UPLOADS
# ============================================================

DATA_UPLOAD_MAX_NUMBER_FIELDS = 10_000


# ============================================================
# WAGTAIL
# ============================================================

WAGTAIL_SITE_NAME = "config"

WAGTAILADMIN_BASE_URL = env(
    "WAGTAILADMIN_BASE_URL",
    "http://127.0.0.1",
)

WAGTAILSEARCH_BACKENDS = {
    "default": {
        "BACKEND": (
            "wagtail.search.backends.database"
        ),
    },
}

WAGTAILDOCS_EXTENSIONS = [
    "csv",
    "docx",
    "key",
    "odt",
    "pdf",
    "pptx",
    "rtf",
    "txt",
    "xlsx",
    "zip",
]


# ============================================================
# SEO
# ============================================================

# Основной адрес сайта: canonical, hreflang, sitemap.xml, Open Graph, JSON-LD.
SEO_BASE_URL = env(
    "SEO_BASE_URL",
    "https://mindtech.kz",
).rstrip("/")

# IndexNow (Bing, Яндекс и др.): уведомление о публикации страниц.
# Ключ — произвольная строка 8–128 символов [A-Za-z0-9-]; сайт отдаёт его
# по адресу /<ключ>.txt. Пустой ключ или INDEXNOW_ENABLED=False — выключено.
INDEXNOW_ENABLED = env_bool(
    "INDEXNOW_ENABLED",
    False,
)

INDEXNOW_KEY = env(
    "INDEXNOW_KEY",
    "",
).strip()

INDEXNOW_ENDPOINT = env(
    "INDEXNOW_ENDPOINT",
    "https://api.indexnow.org/indexnow",
)


# ============================================================
# IIS / REVERSE PROXY
# ============================================================

USE_X_FORWARDED_HOST = env_bool(
    "USE_X_FORWARDED_HOST",
    True,
)

SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)


# ============================================================
# EMAIL
# ============================================================

EMAIL_BACKEND = (
    "django.core.mail.backends.smtp."
    "EmailBackend"
)

EMAIL_HOST = os.getenv(
    "EMAIL_HOST",
    "",
)

EMAIL_PORT = int(
    os.getenv(
        "EMAIL_PORT",
        "465",
    )
)

EMAIL_HOST_USER = os.getenv(
    "EMAIL_HOST_USER",
    "",
)

EMAIL_HOST_PASSWORD = os.getenv(
    "EMAIL_HOST_PASSWORD",
    "",
)

EMAIL_USE_SSL = (
    os.getenv(
        "EMAIL_USE_SSL",
        "False",
    )
    .lower()
    == "true"
)

EMAIL_USE_TLS = (
    os.getenv(
        "EMAIL_USE_TLS",
        "False",
    )
    .lower()
    == "true"
)

DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL",
    EMAIL_HOST_USER,
)

SERVER_EMAIL = EMAIL_HOST_USER

EMAIL_TIMEOUT = 20