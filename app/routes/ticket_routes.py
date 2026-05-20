from flask import Blueprint, render_template_string

tickets_bp = Blueprint("tickets", __name__, url_prefix="/tickets")


@tickets_bp.route("/dashboard")
def dashboard():
    # Pagina temporara - va fi completata dupa ce testam autentificarea.
    return render_template_string(
        """
        <h1>Dashboard tickets</h1>
        <p>Aceasta pagina va fi completata dupa autentificare.</p>
        <a href="/">Inapoi la home</a>
        """
    )