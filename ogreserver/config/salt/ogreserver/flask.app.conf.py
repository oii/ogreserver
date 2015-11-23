# vim: set ft=jinja:
import os
basedir = os.path.abspath(os.path.dirname('..'))


# Celery config
BROKER_URL = "amqp://{{ pillar['rabbitmq_user'] }}:{{ pillar['rabbitmq_pass'] }}@{{ pillar['rabbitmq_host'] }}:5672/{{ pillar['rabbitmq_vhost'] }}"
CELERY_ACCEPT_CONTENT = ['pickle']
CELERY_TIMEZONE = '{{ pillar['timezone'] }}'


# AWS config
AWS_ACCESS_KEY_ID = "{{ pillar.get('aws_access_key', '') }}"
AWS_SECRET_ACCESS_KEY = "{{ pillar.get('aws_secret_key', '') }}"
AWS_REGION = "{{ pillar.get('aws_region', '') }}"
EBOOK_S3_BUCKET = "ogre-ebooks-{{ grains['env'] }}-{{ pillar.get('aws_region', 'local') }}"
STATIC_S3_BUCKET = "ogre-static-{{ grains['env'] }}-{{ pillar.get('aws_region', 'local') }}"

# AWS Advertising API config
AWS_ADVERTISING_API_ACCESS_KEY = "{{ pillar.get('aws_advertising_api_access_key', '') }}"
AWS_ADVERTISING_API_SECRET_KEY = "{{ pillar.get('aws_advertising_api_secret_key', '') }}"
AWS_ADVERTISING_API_ASSOCIATE_TAG = "{{ pillar.get('aws_advertising_api_associate_tag', '') }}"

# Goodreads API key
GOODREADS_API_KEY = "{{ pillar.get('goodreads_api_key', '') }}"


# Flask app
{% if grains['env'] == 'dev' %}
DEBUG = True
STATIC_BASE_URL = "http://{{ grains['ip4_interfaces']['eth0'][0] }}:8880"
{% else %}
DEBUG = False
STATIC_BASE_URL = "https://s3.amazonaws.com"
{% endif %}
BETA = True

# Flask-WTF
SECRET_KEY = "{{ pillar['flask_secret'] }}"

# Main ebook database name
RETHINKDB_DATABASE = 'ogreserver'

# SQLAlchemy DB URI
SQLALCHEMY_DATABASE_URI = "mysql://{{ pillar['mysql_user'] }}:{{ pillar['mysql_pass'] }}@{{ pillar['mysql_host'] }}/{{ pillar['mysql_db'] }}"

# Whoosh full-text search
WHOOSH_BASE = os.path.join(basedir, 'search.db')

# Upload paths
UPLOADED_EBOOKS_DEST = "/srv/{{ pillar['app_directory_name'] }}/uploads"
UPLOADED_LOGS_DEST = "/srv/{{ pillar['app_directory_name'] }}/logs"

# Ebook format definitions
# data structure:
#  is_valid_format (bool): sync to ogreserver
#  is_non_fiction (bool): a PDF-like non-fiction only format

import collections
FormatConfig = collections.namedtuple('FormatConfig', ('is_valid_format', 'is_non_fiction'))

EBOOK_DEFINITIONS = collections.OrderedDict([
    ('mobi', FormatConfig(True, False)),
    ('azw', FormatConfig(True, False)),
    ('azw3', FormatConfig(True, False)),
    ('azw4', FormatConfig(True, True)),
    ('epub', FormatConfig(True, False)),
    ('azw1', FormatConfig(True, False)),
    ('tpz', FormatConfig(True, False)),
    ('pdb', FormatConfig(False, False)),
    ('pdf', FormatConfig(True, True)),
    ('lit', FormatConfig(False, False)),
    ('html', FormatConfig(False, False)),
    ('zip', FormatConfig(False, False)),
])

# Ebook conversion formats; all books will be provided in these formats by OGRE
EBOOK_FORMATS = ['azw3', 'epub']

# OGRE download links expire in 10 seconds
DOWNLOAD_LINK_EXPIRY = 10

# Default number of results for paging on search listing
SEARCH_PAGELEN = 20

# Number of books to convert to epub/azw3 every thirty minutes
NUM_EBOOKS_FOR_CONVERT = 5

# Minimum score to assume a match during fuzzywuzzy text comparison (see models/amazon.py)
AMAZON_FUZZ_THRESHOLD = 50

{% if grains['env'] == 'prod' %}
# Production logging level
import logging
LOGGING_LEVEL = logging.WARNING
{% endif %}


# Site security settings
SECURITY_PASSWORD_SALT = '{{ pillar['password_salt'] }}'
SECURITY_PASSWORD_HASH = 'pbkdf2_sha256'

# Name of HTTP header for ogreclient API
SECURITY_TOKEN_AUTHENTICATION_HEADER = 'Ogre-Key'

# More salts for various password activities
SECURITY_CONFIRM_SALT = 'confirm-{}'.format(SECRET_KEY)
SECURITY_RESET_SALT = 'reset-{}'.format(SECRET_KEY)
SECURITY_LOGIN_SALT = 'login-{}'.format(SECRET_KEY)
SECURITY_CHANGE_SALT = 'change-{}'.format(SECRET_KEY)
SECURITY_REMEMBER_SALT = 'remember-{}'.format(SECRET_KEY)


# Confirmation emails and password reset
SECURITY_CONFIRM_EMAIL_WITHIN = '7 days'
SECURITY_RESET_PASSWORD_WITHIN = '1 days'
SECURITY_LOGIN_WITHOUT_CONFIRMATION = False

# Disable Flask-Security email sends, since ogre does them via Mailgun API on a celery task
SECURITY_SEND_REGISTER_EMAIL = False
SECURITY_SEND_PASSWORD_CHANGE_EMAIL = False
SECURITY_SEND_PASSWORD_RESET_EMAIL = False
SECURITY_SEND_PASSWORD_RESET_NOTICE_EMAIL = False

# Setup subjects for security emails
SECURITY_EMAIL_SUBJECT_CONFIRM = 'Please confirm your email'
SECURITY_EMAIL_SUBJECT_PASSWORD_NOTICE = 'Your password has been reset'
SECURITY_EMAIL_SUBJECT_PASSWORD_CHANGE_NOTICE = 'Your password has been changed'
SECURITY_EMAIL_SUBJECT_PASSWORD_RESET = 'Password reset instructions'

# Mailgun API config
HOSTNAME = 'ogre.oii.yt'
MAILGUN_API_KEY = '{{ pillar.get('mailgun_api_key', '') }}'


# Allow login with username & email
SECURITY_USER_IDENTITY_ATTRIBUTES = ['email', 'username']

# Can reset password, must confirm email, can change password, track logins
SECURITY_RECOVERABLE = True
SECURITY_CONFIRMABLE = True
SECURITY_CHANGEABLE = True
SECURITY_TRACKABLE = True

#SECURITY_UNAUTHORIZED_VIEW = 'core.unauthorized'

SECURITY_MSG_INVALID_PASSWORD = ('Bad username or password', 'error')
SECURITY_MSG_PASSWORD_NOT_PROVIDED = ('Bad username or password', 'error')
SECURITY_MSG_USER_DOES_NOT_EXIST = ('Bad username or password', 'error')
