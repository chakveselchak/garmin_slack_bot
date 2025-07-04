from flask_sqlalchemy import SQLAlchemy
from cryptography.fernet import Fernet
import os

db = SQLAlchemy()
fernet = Fernet(os.environ["FERNET_SECRET_KEY"])

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    slack_user_id = db.Column(db.String, unique=True, nullable=False)
    slack_access_token = db.Column(db.String, nullable=False)
    garmin_email_encrypted = db.Column(db.LargeBinary)
    garmin_password_encrypted = db.Column(db.LargeBinary)

    @property
    def garmin_email(self):
        if self.garmin_email_encrypted:
            return fernet.decrypt(self.garmin_email_encrypted).decode()
        return None

    @garmin_email.setter
    def garmin_email(self, value):
        self.garmin_email_encrypted = fernet.encrypt(value.encode())

    @property
    def garmin_password(self):
        if self.garmin_password_encrypted:
            return fernet.decrypt(self.garmin_password_encrypted).decode()
        return None

    @garmin_password.setter
    def garmin_password(self, value):
        self.garmin_password_encrypted = fernet.encrypt(value.encode())

def init_db():
    db.create_all()
