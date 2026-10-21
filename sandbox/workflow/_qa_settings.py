"""BudgetMe settings used only inside the disposable test container."""
SECRET_KEY = 'local-disposable-test-key'
DEBUG = False
ALLOWED_HOSTS = ['testserver', 'localhost']
INSTALLED_APPS = [
    'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',
    'django.contrib.sites', 'allauth', 'allauth.account', 'allauth.socialaccount',
    'allauth.socialaccount.providers.google', 'budgetbuddy',
]
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:', 'TEST': {'NAME': ':memory:'}}}
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
ROOT_URLCONF = 'BudgetMe.urls'
SITE_ID = 1
MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'APP_DIRS': True,
              'OPTIONS': {'context_processors': [
                  'django.template.context_processors.request',
                  'django.contrib.auth.context_processors.auth',
                  'django.contrib.messages.context_processors.messages',
                  'budgetbuddy.context_processors.auth_providers',
                  'budgetbuddy.context_processors.supabase_realtime',
              ]}}]
AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend', 'allauth.account.auth_backends.AuthenticationBackend']
LOGIN_URL = 'account_login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'account_login'
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_ADAPTER = 'budgetbuddy.adapters.BudgetAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'budgetbuddy.adapters.BudgetSocialAccountAdapter'
SOCIALACCOUNT_PROVIDERS = {'google': {'SCOPE': ['profile', 'email']}}
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
USE_TZ = True
TIME_ZONE = 'Africa/Kampala'
LANGUAGE_CODE = 'en'
STATIC_URL = '/static/'
MEDIA_ROOT = '/tmp/media'
SUPABASE_REALTIME_ENABLED = False
SUPABASE_URL = SUPABASE_ANON_KEY = SUPABASE_JWT_SECRET = ''
GOOGLE_OAUTH_CONFIGURED = False
GOOGLE_CLIENT_ID = GOOGLE_CLIENT_SECRET = GOOGLE_OAUTH_CALLBACK_URI = ''
BUDGETME_CURRENCY = 'UGX'
BUDGETME_COUNTRY = 'Uganda'
