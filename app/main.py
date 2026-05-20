import os
from flask import Flask, jsonify, render_template_string
from app.config import Config, INSTANCE_DIR
from app.database import db, sess
from app.models import User, Ticket, AuditLog, PasswordResetToken


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Creeaza folderul instance/ daca nu exista
    os.makedirs(INSTANCE_DIR, exist_ok=True)

    # Initializare extensii Flask
    db.init_app(app)
    sess.init_app(app)

    # Creeaza automat tabelele definite in models.py
    with app.app_context():
        db.create_all()

    @app.route("/")
    def index():
        return render_template_string(
            """
            <!doctype html>
            <html lang="en">
            <head>
                <meta charset="utf-8">
                <title>Deskly AuthX</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        margin: 40px;
                        background: #f5f5f5;
                    }
                    .card {
                        background: white;
                        padding: 24px;
                        border-radius: 12px;
                        max-width: 700px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
                    }
                    code {
                        background: #eee;
                        padding: 2px 6px;
                        border-radius: 4px;
                    }
                    .badge {
                        display: inline-block;
                        padding: 6px 10px;
                        border-radius: 6px;
                        background: #ffe0e0;
                        color: #8a0000;
                        font-weight: bold;
                    }
                </style>
            </head>
            <body>
                <div class="card">
                    <h1>Deskly AuthX</h1>
                    <p>Aplicatie demonstrativa pentru proiectul DAS.</p>
                    <p>Versiune curenta: <span class="badge">vulnerable</span></p>
                    <p>Scopul aplicatiei este demonstrarea ciclului: build, hack, secure, re-test.</p>
                    <h3>Endpoint-uri disponibile momentan</h3>
                    <ul>
                        <li><code>/</code> - pagina principala</li>
                        <li><code>/health</code> - verificare status aplicatie</li>
                        <li><code>/db-check</code> - verificare tabele create in baza de date</li>
                    </ul>
                </div>
            </body>
            </html>
            """
        )

    @app.route("/health")
    def health():
        return jsonify({
            "status": "ok",
            "app": "Deskly AuthX",
            "version": "vulnerable"
        })

    @app.route("/db-check")
    def db_check():
        # [VULN] Endpoint public care expune structura interna a bazei de date
        return jsonify({
            "status": "ok",
            "database": "connected",
            "tables": {
                "users": User.query.count(),
                "tickets": Ticket.query.count(),
                "audit_logs": AuditLog.query.count(),
                "password_reset_tokens": PasswordResetToken.query.count()
            }
        })

    return app


app = create_app()

if __name__ == "__main__":
    # [VULN] Debug=True expune stack traces si consola interactiva in browser
    app.run(host="127.0.0.1", port=5000, debug=True)