# provides defaults for dev_vars.sls

# app_name is used all over to name directories, config files,
# paths, venvs, databases etc.
app_name: ogreserver

# github repo to clone
app_repo: oii/ogreserver
app_repo_rev: dev

# supervisor program name (defaults to app_name)
#supervisor_name: ogreserver
# virtualenv name
virtualenv_name: ogreserver
# project will be cloned into /srv/<directory_name> (defaults to app_name)
app_directory_name: ogre

# user which runs the app
app_user: ogre

# user which logs into the server (Debian AMI default is admin)
login_user: admin

# gunicorn settings
gunicorn_host: localhost
gunicorn_port: 8005

# postgres settings
db_host: localhost
db_name: ogre
db_user: ogre
db_pass: oii

# flask app settings
flask_secret: its_a_secret
password_salt: eggs

# default OGRE user
ogre_user_name: dev-user
ogre_user_pass: password
ogre_user_email: test@example.com

# ogreclient version
ogreclient_version: 0.0.3

# version of DeDRM tools
dedrm_version: 6.4.1

# watchdog setup for auto-code reloading
watchdog:
  gunicorn:
    pattern: "*.py"
    command: "pkill -HUP gunicorn"
    dir: /srv/ogre
    polling: true
  celeryd:
    pattern: "*/tasks.py;*models/datastore.py"
    command: "sudo supervisorctl restart ogreserver:celeryd.low ogreserver:celeryd.normal ogreserver:celeryd.high"
    dir: /srv/ogre
    polling: true
  sass:
    pattern: "*.scss"
    command: "cd /srv/ogre/static && make sass_dev"
    dir: /srv/ogre/static/sass
    polling: true
  js:
    pattern: "*.js"
    command: "cd /srv/ogre/static && make js_dev"
    dir: /srv/ogre/static/js
    polling: true
  image:
    pattern: "*.*"
    command: "cd /srv/ogre/static && make images"
    dir: /srv/ogre/static/images
    polling: true

# server timezone & locale
timezone: "Europe/London"
locale: en_GB

# install zsh and set as default login shell
shell: zsh

# install extras from apt and install dotfiles
extras:
  - vim
  - zsh
  - git
  - tmux

# install extras from pip
pip:
  - pyflakes
  - ipdb

# set debian APT mirror (ie, ftp.uk)
deb_mirror_prefix: ftp.uk
