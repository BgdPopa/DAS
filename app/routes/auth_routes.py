import hashlib
from flask import Blueprint, request, session, redirect, url_for, render_template, flash
from app.database import db
from app.models import User, AuditLog, PasswordResetToken
from datetime import datetime

auth_bp = Blueprint("auth", __name__)


def log_action(user_id, action, resource=None, resource_id=None):
    # Inregistreaza fiecare actiune importanta in audit_logs
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=str(resource_id) if resource_id else None,
        ip_address=request.remote_addr
    )
    db.session.add(entry)
    db.session.commit()


def md5_hash(password):
    # [VULN] Parola este hash-uita cu MD5 - algoritm slab, fara salt
    return hashlib.md5(password.encode()).hexdigest()


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role", "ANALYST")

        # [VULN] Nu exista validare de lungime sau complexitate a parolei
        existing = User.query.filter_by(email=email).first()
        if existing:
            # [VULN] Mesaj diferit pentru email existent - permite user enumeration
            flash("Email-ul este deja inregistrat.", "danger")
            return render_template("register.html")

        user = User(
            email=email,
            password_hash=md5_hash(password),
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
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if not user:
            # [VULN] Mesaj diferit cand userul nu exista - permite user enumeration
            flash("Contul nu exista.", "danger")
            return render_template("login.html")

        if user.password_hash != md5_hash(password):
            # [VULN] Mesaj diferit cand parola e gresita - permite user enumeration
            flash("Parola incorecta.", "danger")
            log_action(user.id, "LOGIN_FAIL", "auth")
            return render_template("login.html")

        # [VULN] Nu exista rate limiting sau blocare dupa incercari multiple
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
    log_action(user_id, "LOGOUT", "auth")
    # [VULN] Session.clear() nu invalideaza sesiunea server-side complet
    session.clear()
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()

        if not user:
            # [VULN] Mesaj diferit pentru email inexistent - confirma existenta contului
            flash("Email-ul nu este inregistrat.", "danger")
            return render_template("forgot_password.html")

        # [VULN] Token predictibil generat din email + timestamp trunchiat
        raw = f"{email}{int(datetime.utcnow().timestamp()) // 100}"
        token = hashlib.md5(raw.encode()).hexdigest()

        reset = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=None,
            used=False
        )
        db.session.add(reset)
        db.session.commit()

        log_action(user.id, "PASSWORD_RESET_REQUEST", "auth")
        # In productie s-ar trimite pe email - aici il afisam direct pentru PoC
        flash(f"Token resetare: {token}", "info")
        return render_template("forgot_password.html")

    return render_template("forgot_password.html")


@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        token = request.form.get("token")
        new_password = request.form.get("password")

        reset = PasswordResetToken.query.filter_by(token=token).first()

        if not reset:
            flash("Token invalid.", "danger")
            return render_template("reset_password.html")

        # [VULN] Token-ul nu are expirare si poate fi reutilizat
        user = User.query.get(reset.user_id)
        user.password_hash = md5_hash(new_password)
        db.session.commit()

        log_action(user.id, "PASSWORD_RESET_SUCCESS", "auth")
        flash("Parola a fost resetata.", "success")
        return redirect(url_for("auth.login"))

    token = request.args.get("token", "")
    return render_template("reset_password.html", token=token)