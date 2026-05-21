import hashlib
import os
import sys

# Permite rularea scriptului din radacina proiectului, fara erori de import.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import create_app
from app.database import db
from app.models import User, Ticket, AuditLog, PasswordResetToken


def md5_hash(password):
    # [VULN] Folosim MD5 intentionat, ca sa pastram datele compatibile cu versiunea vulnerabila.
    return hashlib.md5(password.encode("utf-8")).hexdigest()


def seed():
    app = create_app()

    with app.app_context():
        # Curatam datele vechi ca fiecare demonstratie sa porneasca de la aceeasi stare.
        PasswordResetToken.query.delete()
        AuditLog.query.delete()
        Ticket.query.delete()
        User.query.delete()
        db.session.commit()

        # Utilizatori de test cu parole slabe, utile pentru PoC.
        user1 = User(
            email="analyst@deskly.com",
            password_hash=md5_hash("123"),
            role="ANALYST"
        )

        user2 = User(
            email="manager@deskly.com",
            password_hash=md5_hash("password"),
            role="MANAGER"
        )

        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()

        # Tichete create pentru user1.
        # Vor fi folosite pentru demonstrarea IDOR: user2 va putea accesa ticketul lui user1.
        ticket1 = Ticket(
            title="Eroare autentificare modul HR",
            description="Utilizatorii nu se pot loga in modulul HR dupa update.",
            severity="HIGH",
            owner_id=user1.id
        )

        ticket2 = Ticket(
            title="Raport lunar generat incorect",
            description="Raportul din luna anterioara contine date duplicate.",
            severity="MED",
            owner_id=user1.id
        )

        # Ticket creat pentru user2, ca sa existe date diferite intre utilizatori.
        ticket3 = Ticket(
            title="Acces dashboard indisponibil",
            description="Managerul nu poate accesa dashboard-ul de management.",
            severity="HIGH",
            owner_id=user2.id
        )

        db.session.add_all([ticket1, ticket2, ticket3])
        db.session.commit()

        print("Seed complet:")
        print(f"  user1: analyst@deskly.com / 123 (id={user1.id})")
        print(f"  user2: manager@deskly.com / password (id={user2.id})")
        print("  tichete create: 3")
        print("")
        print("Date utile pentru testare:")
        print("  - parola 123 este stocata ca MD5")
        print("  - user2 poate incerca accesarea directa a /tickets/1 pentru IDOR")
        print("  - cautarea poate fi testata cu payload SQL injection")


if __name__ == "__main__":
    seed()