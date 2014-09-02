app_name: ogreserver
app_user: vagrant
app_repo: oii/ogre
app_repo_rev: develop
login_user: vagrant

gunicorn_host: localhost
gunicorn_port: 8005

mysql_host: localhost
mysql_db: ogre
mysql_user: ogreserver
mysql_pass: drm_sucks_anus

rabbitmq_host: localhost
rabbitmq_vhost: dev
rabbitmq_user: dev
rabbitmq_pass: dev

flask_secret: its_a_secret
aws_access_key: ""
aws_secret_key: ""
aws_region: ap-southeast-2
s3_bucket: oii-ogre-dev

aws_advertising_api_access_key: ""
aws_advertising_api_secret_key: ""
aws_advertising_api_associate_tag: ""

ogre_user_name: test
ogre_user_pass: test
ogre_user_email: test@example.come

watchdog:
  gunicorn:
    pattern: "*.py"
    command: "kill -HUP $(cat /tmp/gunicorn-ogreserver.pid)"
    dir: /srv/ogreserver/ogreserver
  celeryd:
    pattern: "*/tasks.py"
    command: "sudo supervisorctl restart ogreserver:celeryd"
    dir: /srv/ogreserver/ogreserver

timezone: "Australia/Melbourne"

# get dotfiles from github
github_username: mafrosis
# install zsh and set as default login shell
shell: zsh

# install extras from apt
extras:
  - vim
  - zsh
  - tmux
  - git

# install extras from pip
pip:
  - pyflakes
  - virtualenvwrapper

# set backports to AU in bit.ly/19Nso9M
deb_mirror_prefix: ftp.au
