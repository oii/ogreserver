# setup a dev OGRE user
create-ogre-user:
  cmd.run:
    - name: /var/cache/ogre/venv/bin/python manage.py create_user {{ pillar['ogre_user_name'] }} {{ pillar['ogre_user_pass'] }} {{ pillar['ogre_user_email'] }} --role=admin --confirmed
    - cwd: /srv/ogre
    - user: {{ pillar['app_user'] }}
    - require:
      - postgres_privileges: {{ pillar['db_user'] }}
