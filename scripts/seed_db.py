import os
import sys
import bcrypt

# Permite rularea scriptului din radacina proiectului, fara erori de import.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import create_app
from app.database import db
from app.models import User, Ticket, AuditLog, PasswordResetToken


def hash_password(password):
    # [SECURE] Seed-ul pentru branch-ul secure foloseste bcrypt, nu MD5.
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(rounds=12)
    ).decode("utf-8")


def seed():
    app = create_app()

    with app.app_context():
        # Curatam datele vechi ca fiecare demonstratie sa porneasca de la aceeasi stare.
        PasswordResetToken.query.delete()
        AuditLog.query.delete()
        Ticket.query.delete()
        User.query.delete()
        db.session.commit()

        # Utilizatori de test compatibili cu autentificarea securizata.
        analyst = User(
            email="analyst@deskly.com",
            password_hash=hash_password("Analyst@1234"),
            role="ANALYST",
            failed_login_attempts=0,
            locked=False,
            locked_until=None
        )

        manager = User(
            email="manager@deskly.com",
            password_hash=hash_password("Manager@1234"),
            role="MANAGER",
            failed_login_attempts=0,
            locked=False,
            locked_until=None
        )

        db.session.add_all([analyst, manager])
        db.session.commit()

        # Tichete create pentru analyst.
        ticket1 = Ticket(
            title="Eroare autentificare modul HR",
            description="Utilizatorii nu se pot loga in modulul HR dupa update.",
            severity="HIGH",
            status="OPEN",
            owner_id=analyst.id
        )

        ticket2 = Ticket(
            title="Raport lunar generat incorect",
            description="Raportul din luna anterioara contine date duplicate.",
            severity="MED",
            status="OPEN",
            owner_id=analyst.id
        )

        # Ticket creat pentru manager, ca sa existe date diferite intre utilizatori.
        ticket3 = Ticket(
            title="Acces dashboard indisponibil",
            description="Managerul nu poate accesa dashboard-ul de management.",
            severity="HIGH",
            status="OPEN",
            owner_id=manager.id
        )

        db.session.add_all([ticket1, ticket2, ticket3])
        db.session.commit()

        print("Seed secure complet:")
        print(f"  analyst: analyst@deskly.com / Analyst@1234 (id={analyst.id})")
        print(f"  manager: manager@deskly.com / Manager@1234 (id={manager.id})")
        print("  tichete create: 3")
        print("")
        print("Date utile pentru re-testare secure:")
        print("  - parolele sunt stocate cu bcrypt")
        print("  - analyst vede doar ticketele lui")
        print("  - manager vede doar ticketul lui si poate accesa audit logs")
        print("  - IDOR se testeaza prin accesarea /tickets/3 ca analyst")
        print("  - SQL injection se testeaza cu payload: ' OR 1=1 --")


if __name__ == "__main__":
    seed()