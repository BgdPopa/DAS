import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
DATABASE_PATH = os.path.join(INSTANCE_DIR, "deskly_authx.db")


class Config:
    # [SECURE] Cheia secreta este citita din variabila de mediu.
    # Fallback-ul este pastrat doar pentru rularea locala in laborator.
    SECRET_KEY = os.environ.get("SECRET_KEY", "schimba-asta-in-productie")

    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_TYPE = "filesystem"

    # [SECURE] HttpOnly blocheaza accesul JavaScript la cookie-ul de sesiune.
    SESSION_COOKIE_HTTPONLY = True

    # [SECURE] Secure=False este pastrat doar pentru testarea locala pe HTTP.
    # In productie, cu HTTPS, aceasta valoare trebuie setata la True.
    SESSION_COOKIE_SECURE = False

    # [SECURE] SameSite=Strict previne trimiterea cookie-ului in cereri cross-site.
    SESSION_COOKIE_SAMESITE = "Strict"

    # [SECURE] Sesiunea expira dupa 30 de minute.
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)

    # [SECURE] Debug-ul este dezactivat in versiunea securizata.
    DEBUG = False