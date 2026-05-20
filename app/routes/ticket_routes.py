from functools import wraps

from flask import Blueprint, request, session, redirect, url_for, render_template, flash

from app.database import db
from app.models import Ticket
from app.routes.auth_routes import log_action


tickets_bp = Blueprint("tickets", __name__, url_prefix="/tickets")


def login_required(f):
    # Verificam daca utilizatorul este autentificat inainte de a accesa ruta.
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))

        return f(*args, **kwargs)

    return decorated


@tickets_bp.route("/dashboard")
@login_required
def dashboard():
    # [VULN] Returnam toate ticketele, nu doar cele ale utilizatorului curent.
    tickets = Ticket.query.all()
    return render_template("dashboard.html", tickets=tickets)


@tickets_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        severity = request.form.get("severity", "LOW")

        ticket = Ticket(
            title=title,
            description=description,
            severity=severity,
            owner_id=session["user_id"]
        )

        db.session.add(ticket)
        db.session.commit()

        log_action(session["user_id"], "CREATE_TICKET", "ticket", ticket.id)

        flash("Ticket creat cu succes.", "success")
        return redirect(url_for("tickets.dashboard"))

    return render_template("create_ticket.html")


@tickets_bp.route("/<int:ticket_id>")
@login_required
def view(ticket_id):
    # [VULN] Nu verificam daca ticketul apartine utilizatorului curent - IDOR.
    ticket = Ticket.query.get_or_404(ticket_id)

    log_action(session["user_id"], "VIEW_TICKET", "ticket", ticket_id)

    return render_template("view_ticket.html", ticket=ticket)


@tickets_bp.route("/<int:ticket_id>/edit", methods=["GET", "POST"])
@login_required
def edit(ticket_id):
    # [VULN] Orice utilizator autentificat poate edita orice ticket dupa ID - IDOR.
    ticket = Ticket.query.get_or_404(ticket_id)

    if request.method == "POST":
        ticket.title = request.form.get("title")
        ticket.description = request.form.get("description")
        ticket.severity = request.form.get("severity", ticket.severity)
        ticket.status = request.form.get("status", ticket.status)

        db.session.commit()

        log_action(session["user_id"], "EDIT_TICKET", "ticket", ticket_id)

        flash("Ticket actualizat.", "success")
        return redirect(url_for("tickets.dashboard"))

    return render_template("edit_ticket.html", ticket=ticket)


@tickets_bp.route("/search")
@login_required
def search():
    query = request.args.get("q", "")

    # [VULN] Query concatenat direct - vulnerabil la SQL injection.
    results = db.session.execute(
        db.text(
            f"SELECT * FROM tickets "
            f"WHERE title LIKE '%{query}%' OR description LIKE '%{query}%'"
        )
    ).fetchall()

    log_action(session["user_id"], "SEARCH_TICKETS", "ticket")

    return render_template("search_tickets.html", results=results, query=query)