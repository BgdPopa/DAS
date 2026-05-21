from functools import wraps

from flask import Blueprint, render_template, session, redirect, url_for, flash

from app.models import AuditLog, User


audit_bp = Blueprint("audit", __name__, url_prefix="/audit")


def manager_required(f):
    # [SECURE] Doar utilizatorii cu rol MANAGER pot accesa rutele de audit.
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))

        if session.get("role") != "MANAGER":
            flash("Acces restrictionat. Doar managerii pot vedea logurile.", "danger")
            return redirect(url_for("tickets.dashboard"))

        return f(*args, **kwargs)

    return decorated


@audit_bp.route("/logs")
@manager_required
def logs():
    # [SECURE] Accesul la audit logs este restrictionat la rolul MANAGER.
    all_logs = (
        AuditLog.query
        .order_by(AuditLog.timestamp.desc())
        .limit(100)
        .all()
    )

    users = User.query.all()
    users_by_id = {user.id: user.email for user in users}

    return render_template(
        "audit_logs.html",
        logs=all_logs,
        users_by_id=users_by_id
    )