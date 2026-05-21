import os

from flask import Flask, jsonify, render_template_string

from app.config import Config, INSTANCE_DIR
from app.database import db, sess


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(INSTANCE_DIR, exist_ok=True)

    db.init_app(app)
    sess.init_app(app)

    with app.app_context():
        db.create_all()

    from app.routes.auth_routes import auth_bp
    from app.routes.ticket_routes import tickets_bp
    from app.routes.audit_routes import audit_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(tickets_bp)
    app.register_blueprint(audit_bp)

    @app.route("/")
    def index():
        return render_template_string("""
            <!doctype html>
            <html lang="en">
            <head>
                <meta charset="utf-8">
                <title>Deskly AuthX</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                    .card { background: white; padding: 24px; border-radius: 12px;
                            max-width: 700px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); }
                    code { background: #eee; padding: 2px 6px; border-radius: 4px; }
                    .badge { display: inline-block; padding: 6px 10px; border-radius: 6px;
                             background: #e0f0e0; color: #1a5c1a; font-weight: bold; }
                </style>
            </head>
            <body>
                <div class="card">
                    <h1>Deskly AuthX</h1>
                    <p>Aplicatie demonstrativa pentru proiectul DAS.</p>
                    <p>Versiune curenta: <span class="badge">secure</span></p>
                    <p>Scopul aplicatiei este demonstrarea ciclului: build, hack, secure, re-test.</p>

                    <h3>Endpoint-uri disponibile</h3>
                    <ul>
                        <li><code>/</code> - pagina principala</li>
                        <li><code>/health</code> - verificare status aplicatie</li>
                        <li><code>/register</code> - inregistrare utilizator</li>
                        <li><code>/login</code> - autentificare</li>
                    </ul>
                </div>
            </body>
            </html>
        """)

    @app.route("/health")
    def health():
        return jsonify({
            "status": "ok",
            "app": "Deskly AuthX",
            "version": "secure"
        })

    # [SECURE] /db-check a fost eliminat.
    # In versiunea vulnerabila, acest endpoint expunea structura bazei de date.

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Resursa nu a fost gasita."}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Eroare interna. Contactati administratorul."}), 500

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=app.config.get("DEBUG", False)
    )