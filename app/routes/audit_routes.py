from flask import Blueprint, render_template_string

audit_bp = Blueprint("audit", __name__, url_prefix="/audit")


@audit_bp.route("/logs")
def logs():
    # Pagina temporara - va fi completata ulterior cu evenimentele din audit_logs.
    return render_template_string(
        """
        <h1>Audit Logs</h1>
        <p>Aceasta pagina va fi completata ulterior.</p>
        <a href="/">Inapoi la home</a>
        """
    )