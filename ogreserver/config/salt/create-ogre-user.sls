# setup a dev OGRE user
ogre-create-user:
  cmd.run:
    - name: bin/python manage.py create_user {{ pillar['ogre_user_name'] }} {{ pillar['ogre_user_pass'] }} {{ pillar['ogre_user_email'] }} --role=admin --confirmed
    - cwd: /srv/ogre
    - unless: bin/python manage.py create_user {{ pillar['ogre_user_name'] }} null null --test
    - user: {{ pillar['app_user'] }}
