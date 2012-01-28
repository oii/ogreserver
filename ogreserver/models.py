from flaskext.login import UserMixin

from passlib.context import CryptContext

from ogreserver import app, db

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(64))
    email = db.Column(db.String(120), unique=True)

    def __init__(self, username, password, email):
        self.username = username
        self.password = pwd_context.encrypt(password)
        self.email = email

    @staticmethod
    def authenticate(username, password):
        user = User.query.filter_by(username=username).first()
        if not user:
            return None
        elif pwd_context.verify(password, user.password) is False:
            return None
        return user

    # Flask-Login method
    def is_authenticated(self):
        if self.email is not None:
            return True
        else:
            return False


pwd_context = CryptContext(
    schemes=["pbkdf2_sha256", "des_crypt" ],
    default="pbkdf2_sha256",
    all__vary_rounds = "10%",
    pbkdf2_sha256__default_rounds = 8000,
)

