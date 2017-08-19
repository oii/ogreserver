# create a special OGREBOT user
create-ogrebot-user:
  cmd.run:
    - name: /var/cache/ogre/venv/bin/python manage.py create_user ogrebot ogrebot ogrebot@ogre.oii.yt --role=admin
    - cwd: /srv/ogre
    - unless: /var/cache/ogre/venv/bin/python manage.py create_user ogrebot null null --test
    - user: {{ pillar['app_user'] }}
    - require:
      - cmd: ogre-init
