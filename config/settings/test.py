# test.py
from .local import *

DEBUG = True
TESTING = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test_app_db.sqlite3",
    }
}