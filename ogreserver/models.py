from datetime import datetime

from flask.ext.login import UserMixin

from passlib.context import CryptContext

from ogreserver import app, db


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(256))
    email = db.Column(db.String(120), unique=True)
    display_name = db.Column(db.String(50), unique=True)
    api_key_expires = db.Column(db.DateTime)

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

    @staticmethod
    def _compile_pre_key(username, password, timestamp):
        # construct a unique identifier to be hashed
        return "%s:%s:%s:%s" % (app.config['SECRET_KEY'], username, password, timestamp)

    @staticmethod
    def create_auth_key(username, password, timestamp):
        # hash the value from _compile_pre_key()
        return pwd_context.encrypt(User._compile_pre_key(username, password, timestamp))

    @staticmethod
    def validate_auth_key(username, api_key):
        print username
        # load the user by name
        user = User.query.filter_by(username=username).first()
        if not user:
            return None

        # TODO check API key hasn't expired

        print username
        print api_key

        # reconstruct the key and verify it
        prekey = User._compile_pre_key(user.username, user.password, user.api_key_expires)
        if pwd_context.verify(prekey, api_key) is True:
            return user
        else:
            return None

    def assign_auth_key(self):
        # generate a new API key and save against the user
        self.api_key_expires = datetime.utcnow()
        api_key = User.create_auth_key(self.username, self.password, self.api_key_expires)
        db.session.add(self)
        db.session.commit()
        return api_key

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

