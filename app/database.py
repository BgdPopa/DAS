from flask_sqlalchemy import SQLAlchemy
from flask_session import Session

# Instantele extensions - initializate fara app, legate in create_app()
db = SQLAlchemy()
sess = Session()