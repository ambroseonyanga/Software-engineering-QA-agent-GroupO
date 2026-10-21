# Isolated settings for BudgetMe's service tests.
# Do not import BudgetMe.settings or load its .env file.

SECRET_KEY = "sandbox-only-key-not-for-production"
DEBUG = False

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "budgetbuddy",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "TEST": {
            "NAME": ":memory:",
        },
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

USE_TZ = True
TIME_ZONE = "Africa/Kampala"
LANGUAGE_CODE = "en"

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# External integrations are disabled for these tests.
SUPABASE_REALTIME_ENABLED = False
SUPABASE_URL = ""
SUPABASE_ANON_KEY = ""
SUPABASE_JWT_SECRET = ""

GOOGLE_OAUTH_CONFIGURED = False
GOOGLE_CLIENT_ID = ""
GOOGLE_CLIENT_SECRET = ""

BUDGETME_CURRENCY = "UGX"
BUDGETME_COUNTRY = "Uganda"