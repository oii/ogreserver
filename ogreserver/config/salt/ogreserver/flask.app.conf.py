# vim: set ft=jinja:
import os
basedir = os.path.abspath(os.path.dirname('..'))

# Celery config
BROKER_URL = "amqp://{{ pillar['rabbitmq_user'] }}:{{ pillar['rabbitmq_pass'] }}@{{ pillar['rabbitmq_host'] }}:5672/{{ pillar['rabbitmq_vhost'] }}"

CELERY_DEFAULT_QUEUE = 'ogreserver'
CELERY_DEFAULT_EXCHANGE = 'ogreserver'
CELERY_DEFAULT_EXCHANGE_TYPE = 'direct'
CELERY_DEFAULT_ROUTING_KEY = 'ogreserver'
CELERY_ACCEPT_CONTENT = ['pickle']

# AWS config
AWS_ACCESS_KEY = "{{ pillar['aws_access_key'] }}"
AWS_SECRET_KEY = "{{ pillar['aws_secret_key'] }}"
AWS_REGION = "{{ pillar['aws_region'] }}"
S3_BUCKET = "{{ pillar['s3_bucket'] }}"

# AWS Advertising API config
AWS_ADVERTISING_API_ACCESS_KEY = "{{ pillar.get('aws_advertising_api_access_key', '') }}"
AWS_ADVERTISING_API_SECRET_KEY = "{{ pillar.get('aws_advertising_api_secret_key', '') }}"
AWS_ADVERTISING_API_ASSOCIATE_TAG = "{{ pillar.get('aws_advertising_api_associate_tag', '') }}"

# Flask app
{% if grains['env'] == 'dev' %}
DEBUG = True
{% else %}
DEBUG = False
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
UPLOADED_EBOOKS_DEST = "/srv/{{ pillar['app_name'] }}/uploads"
UPLOADED_LOGS_DEST = "/srv/{{ pillar['app_name'] }}/logs"

# Ebook conversion formats; all books will be provided in these formats by OGRE
EBOOK_FORMATS = ['mobi', 'azw', 'epub', 'pdf']

# OGRE download links expire in 10 seconds
DOWNLOAD_LINK_EXPIRY = 10

{% if grains['env'] == 'prod' %}
# Production logging level
import logging
LOGGING_LEVEL = logging.WARNING
{% endif %}
