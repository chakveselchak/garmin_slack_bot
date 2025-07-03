from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slack_user_id = db.Column(db.String, unique=True, nullable=False)
    slack_access_token = db.Column(db.String, nullable=False)
    garmin_email = db.Column(db.String)
    garmin_password = db.Column(db.String)

def init_db():
    db.create_all()
