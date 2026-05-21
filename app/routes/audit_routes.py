from flask import Blueprint, render_template, session, redirect, url_for

from app.models import AuditLog, User


audit_bp = Blueprint("audit", __name__, url_prefix="/audit")


def audit_login_required():
    # Verificare simpla pentru ca pagina de audit sa nu fie accesibila fara login.
    return "user_id" in session


@audit_bp.route("/logs")
def logs():
    if not audit_login_required():
        return redirect(url_for("auth.login"))

    # [VULN] In versiunea vulnerabila, orice utilizator autentificat poate vedea toate logurile.
    # In versiunea securizata, accesul ar trebui limitat doar pentru rolul MANAGER/Admin.
    logs = (
        AuditLog.query
        .order_by(AuditLog.timestamp.desc())
        .limit(100)
        .all()
    )

    users = User.query.all()
    users_by_id = {user.id: user.email for user in users}

    return render_template(
        "audit_logs.html",
        logs=logs,
        users_by_id=users_by_id
    )