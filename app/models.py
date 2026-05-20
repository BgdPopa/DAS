from datetime import datetime
from app.database import db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    # [VULN] Parola stocata ca MD5 in loc de bcrypt
    password_hash = db.Column(db.String(255), nullable=False)
    # Roluri posibile: ANALYST, MANAGER
    role = db.Column(db.String(20), nullable=False, default="ANALYST")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Folosit pentru blocarea contului dupa brute force
    locked = db.Column(db.Boolean, default=False)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)

    tickets = db.relationship("Ticket", backref="owner", lazy=True)
    audit_logs = db.relationship("AuditLog", backref="user", lazy=True)


class Ticket(db.Model):
    __tablename__ = "tickets"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    # Valori posibile: LOW, MED, HIGH
    severity = db.Column(db.String(10), nullable=False, default="LOW")
    # Valori posibile: OPEN, IN_PROGRESS, RESOLVED
    status = db.Column(db.String(20), nullable=False, default="OPEN")
    # [VULN] owner_id neprotejat - permite IDOR in v1
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(50), nullable=False)
    resource = db.Column(db.String(50), nullable=True)
    resource_id = db.Column(db.String(50), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)


class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    # [VULN] Token generat simplu, predictibil si reutilizabil in v1
    token = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    used = db.Column(db.Boolean, default=False)
    used_at = db.Column(db.DateTime, nullable=True)