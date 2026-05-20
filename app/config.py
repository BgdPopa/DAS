import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
DATABASE_PATH = os.path.join(INSTANCE_DIR, "deskly_authx.db")

class Config:
    # [VULN] Cheie hardcodata ca fallback - in v2 doar din .env, fara fallback
    SECRET_KEY = os.environ.get("SECRET_KEY", "vulnerable-dev-secret-key")

    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_TYPE = "filesystem"

    # [VULN] Cookie-uri fara flags de securitate
    # HttpOnly=False permite accesului JavaScript la cookie (risc XSS)
    SESSION_COOKIE_HTTPONLY = False
    # Secure=False permite transmiterea pe HTTP necriptat
    SESSION_COOKIE_SECURE = False
    # SameSite=None expune sesiunea la atacuri CSRF
    SESSION_COOKIE_SAMESITE = None

    # [VULN] Sesiune valabila 7 zile - interval prea lung
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)