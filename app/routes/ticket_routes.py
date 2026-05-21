from functools import wraps

from flask import Blueprint, request, session, redirect, url_for, render_template, flash
from sqlalchemy import or_

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


def get_owned_ticket_or_none(ticket_id):
    # [SECURE] Ticketul este incarcat dupa ID, apoi verificam explicit proprietarul.
    # Daca ticketul nu apartine utilizatorului curent, accesul este refuzat logic.
    ticket = Ticket.query.get_or_404(ticket_id)

    if ticket.owner_id != session["user_id"]:
        log_action(session["user_id"], "UNAUTHORIZED_TICKET_ACCESS", "ticket", ticket_id)
        return None

    return ticket


@tickets_bp.route("/dashboard")
@login_required
def dashboard():
    # [SECURE] Utilizatorul vede doar ticketele proprii, nu toate ticketele din baza de date.
    tickets = (
        Ticket.query
        .filter_by(owner_id=session["user_id"])
        .order_by(Ticket.id.desc())
        .all()
    )

    return render_template("dashboard.html", tickets=tickets)


@tickets_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        severity = request.form.get("severity", "LOW")

        if not title or not description:
            flash("Titlul si descrierea sunt obligatorii.", "danger")
            return render_template("create_ticket.html")

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
    # [SECURE] Prevenim IDOR: doar proprietarul ticketului il poate vedea.
    ticket = get_owned_ticket_or_none(ticket_id)

    if ticket is None:
        flash("Nu ai acces la acest ticket.", "danger")
        return redirect(url_for("tickets.dashboard"))

    log_action(session["user_id"], "VIEW_TICKET", "ticket", ticket_id)

    return render_template("view_ticket.html", ticket=ticket)


@tickets_bp.route("/<int:ticket_id>/edit", methods=["GET", "POST"])
@login_required
def edit(ticket_id):
    # [SECURE] Prevenim IDOR: doar proprietarul ticketului il poate edita.
    ticket = get_owned_ticket_or_none(ticket_id)

    if ticket is None:
        flash("Nu ai acces la acest ticket.", "danger")
        return redirect(url_for("tickets.dashboard"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()

        if not title or not description:
            flash("Titlul si descrierea sunt obligatorii.", "danger")
            return render_template("edit_ticket.html", ticket=ticket)

        ticket.title = title
        ticket.description = description
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
    query = request.args.get("q", "").strip()

    # [SECURE] Query construit prin SQLAlchemy ORM, nu prin concatenare directa de SQL.
    # Payload-uri precum ' OR 1=1 -- sunt tratate ca text simplu, nu ca instructiuni SQL.
    base_query = Ticket.query.filter_by(owner_id=session["user_id"])

    if query:
        pattern = f"%{query}%"
        results = (
            base_query
            .filter(
                or_(
                    Ticket.title.ilike(pattern),
                    Ticket.description.ilike(pattern)
                )
            )
            .order_by(Ticket.id.desc())
            .all()
        )
    else:
        results = base_query.order_by(Ticket.id.desc()).all()

    log_action(session["user_id"], "SEARCH_TICKETS", "ticket")

    return render_template("search_tickets.html", results=results, query=query)