# local.py
from .prd import *

DEBUG = True

DATABASES["default"]["OPTIONS"]["sslmode"] = "disable"