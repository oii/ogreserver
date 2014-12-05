{% import_yaml "default_vars.sls" as defaults %}

# app_name is used all over to name directories, config files,
# paths, venvs, databases etc.
app_name: {{ defaults.app_name }}

# github repo to clone
app_repo: ""
app_repo_rev: {{ defaults.app_repo_rev }}

# project will be cloned into /srv/<directory_name> (defaults to app_name)
app_directory_name: {{ defaults.app_directory_name }}

# user which runs the app
app_user: vagrant
# user which logs into the server
login_user: vagrant

# gunicorn settings
gunicorn_host: {{ defaults.gunicorn_host }}
gunicorn_port: {{ defaults.gunicorn_port }}

# mysql settings
mysql_host: {{ defaults.mysql_host }}
mysql_db: {{ defaults.mysql_db }}
mysql_user: {{ defaults.mysql_user }}
mysql_pass: {{ defaults.mysql_pass }}

# rabbitmq settings
rabbitmq_host: {{ defaults.rabbitmq_host }}
rabbitmq_vhost: {{ defaults.rabbitmq_vhost }}
rabbitmq_user: {{ defaults.rabbitmq_user }}
rabbitmq_pass: {{ defaults.rabbitmq_pass }}

# flask app settings
flask_secret: {{ defaults.flask_secret }}
password_salt: {{ defaults.password_salt }}
s3_bucket: ogre-dev

aws_advertising_api_access_key: ""
aws_advertising_api_secret_key: ""
aws_advertising_api_associate_tag: ""

# default OGRE user
ogre_user_name: {{ defaults.ogre_user_name }}
ogre_user_pass: {{ defaults.ogre_user_pass }}
ogre_user_email: {{ defaults.ogre_user_email }}

# watchdog setup for auto-code reloading
watchdog:
  gunicorn:
    pattern: "*.py"
    command: "kill -HUP $(cat /tmp/gunicorn-ogreserver.pid)"
    dir: /srv/ogre/ogreserver
  celeryd:
    pattern: "*/tasks.py"
    command: "sudo supervisorctl restart ogreserver:celeryd"
    dir: /srv/ogre/ogreserver


# server timezone & locale
timezone: {{ defaults.timezone }}
locale: {{ defaults.locale }}
hostname: ogreserver

# get dotfiles from github
github_username: {{ defaults.github_username }}

# install zsh and set as default login shell
shell: {{ defaults.shell }}

# install extras from apt and install dotfiles
extras:
{% for name in defaults.extras %}
  - {{ name }}
{% endfor %}

# install extras from pip
pip:
{% for name in defaults.pip %}
  - {{ name }}
{% endfor %}

# set backports to AU in bit.ly/19Nso9M
deb_mirror_prefix: {{ defaults.deb_mirror_prefix }}

# your github key
github_key: |
  -----BEGIN RSA PRIVATE KEY-----
  -----END RSA PRIVATE KEY-----
