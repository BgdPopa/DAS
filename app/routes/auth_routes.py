import bcrypt
import secrets
from datetime import datetime, timedelta

from flask import Blueprint, request, session, redirect, url_for, render_template, flash

from app.database import db
from app.models import User, AuditLog, PasswordResetToken


auth_bp = Blueprint("auth", __name__)


def log_action(user_id, action, resource=None, resource_id=None):
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=str(resource_id) if resource_id else None,
        ip_address=request.remote_addr
    )
    db.session.add(entry)
    db.session.commit()


def hash_password(password):
    # [SECURE] bcrypt genereaza automat salt si aplica un cost computational.
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def check_password(password, password_hash):
    # [SECURE] Compararea parolei se face prin bcrypt.checkpw.
    # Daca exista inca hash-uri vechi MD5 in DB, bcrypt poate da eroare; tratam cazul ca login esuat.
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8")
        )
    except ValueError:
        return False


def validate_password(password):
    # [SECURE] Politica minima de parola pentru versiunea securizata.
    if not password:
        return False, "Parola este obligatorie."

    if len(password) < 8:
        return False, "Parola trebuie sa aiba cel putin 8 caractere."

    if not any(ch.islower() for ch in password):
        return False, "Parola trebuie sa contina cel putin o litera mica."

    if not any(ch.isupper() for ch in password):
        return False, "Parola trebuie sa contina cel putin o litera mare."

    if not any(ch.isdigit() for ch in password):
        return False, "Parola trebuie sa contina cel putin o cifra."

    if not any(not ch.isalnum() for ch in password):
        return False, "Parola trebuie sa contina cel putin un caracter special."

    weak_passwords = {
        "password",
        "password123",
        "12345678",
        "qwerty123",
        "admin123",
        "test1234"
    }

    if password.lower() in weak_passwords:
        return False, "Parola este prea usor de ghicit."

    return True, ""


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "ANALYST")

        valid, message = validate_password(password)
        if not valid:
            flash(message, "danger")
            return render_template("register.html")

        existing = User.query.filter_by(email=email).first()
        if existing:
            # [SECURE] Mesaj neutru, fara detalii suplimentare despre existenta contului.
            flash("Nu se poate crea contul cu datele introduse.", "danger")
            return render_template("register.html")

        user = User(
            email=email,
            password_hash=hash_password(password),
            role=role
        )

        db.session.add(user)
        db.session.commit()

        log_action(user.id, "REGISTER", "auth")
        flash("Cont creat cu succes.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        # [SECURE] Mesaj unic pentru cont inexistent si parola gresita.
        generic_error = "Email sau parola incorecta."

        if not user:
            flash(generic_error, "danger")
            return render_template("login.html")

        # [SECURE] Daca perioada de blocare a expirat, contul este deblocat automat.
        if user.locked and user.locked_until and user.locked_until <= datetime.utcnow():
            user.locked = False
            user.locked_until = None
            user.failed_login_attempts = 0
            db.session.commit()

        # [SECURE] Daca userul este inca blocat temporar, nu mai verificam parola.
        if user.locked and user.locked_until and user.locked_until > datetime.utcnow():
            flash("Contul este temporar blocat. Incearca din nou mai tarziu.", "danger")
            return render_template("login.html")

        if not check_password(password, user.password_hash):
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1

            if user.failed_login_attempts >= 5:
                user.locked = True
                user.locked_until = datetime.utcnow() + timedelta(minutes=15)

            db.session.commit()
            log_action(user.id, "LOGIN_FAIL", "auth")

            flash(generic_error, "danger")
            return render_template("login.html")

        # [SECURE] Resetam incercarile esuate dupa autentificare reusita.
        user.failed_login_attempts = 0
        user.locked = False
        user.locked_until = None
        db.session.commit()

        session.clear()
        session["user_id"] = user.id
        session["email"] = user.email
        session["role"] = user.role
        session.permanent = True

        log_action(user.id, "LOGIN_SUCCESS", "auth")
        return redirect(url_for("tickets.dashboard"))

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    user_id = session.get("user_id")

    if user_id:
        log_action(user_id, "LOGOUT", "auth")

    session.clear()
    flash("Ai fost delogat.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()

        # [SECURE] Mesaj neutru pentru a evita user enumeration.
        generic_message = "Daca adresa exista in sistem, a fost generat un token de resetare."

        if not user:
            flash(generic_message, "info")
            return render_template("forgot_password.html")

        # [SECURE] Token criptografic random, nu MD5 predictibil.
        token = secrets.token_urlsafe(32)

        reset = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(minutes=15),
            used=False
        )

        db.session.add(reset)
        db.session.commit()

        log_action(user.id, "PASSWORD_RESET_REQUEST", "auth")

        # In laborator il afisam ca sa putem testa fluxul.
        # In productie, token-ul ar trebui trimis prin email.
        flash(f"Token resetare: {token}", "info")
        return render_template("forgot_password.html")

    return render_template("forgot_password.html")


@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        token = request.form.get("token", "").strip()
        new_password = request.form.get("password", "")

        reset = PasswordResetToken.query.filter_by(token=token).first()

        if (
            not reset
            or reset.used
            or reset.expires_at is None
            or reset.expires_at < datetime.utcnow()
        ):
            flash("Token invalid sau expirat.", "danger")
            return render_template("reset_password.html")

        valid, message = validate_password(new_password)
        if not valid:
            flash(message, "danger")
            return render_template("reset_password.html", token=token)

        user = User.query.get(reset.user_id)
        if not user:
            flash("Token invalid sau expirat.", "danger")
            return render_template("reset_password.html")

        user.password_hash = hash_password(new_password)

        # [SECURE] Token-ul devine one-time use dupa prima utilizare.
        reset.used = True

        # [SECURE] Dupa resetarea parolei, resetam si starea de lockout.
        user.failed_login_attempts = 0
        user.locked = False
        user.locked_until = None

        db.session.commit()

        log_action(user.id, "PASSWORD_RESET_SUCCESS", "auth")
        flash("Parola a fost resetata.", "success")
        return redirect(url_for("auth.login"))

    token = request.args.get("token", "")
    return render_template("reset_password.html", token=token)