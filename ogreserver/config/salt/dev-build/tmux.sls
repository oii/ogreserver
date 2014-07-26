#
# Extra tmux configuration for dev-builds
#

# install tmux segments for gunicorn & celeryd state
{% for app in ('gunicorn', 'celeryd') %}
tmux-{{ app }}-segment:
  file.managed:
    - name: /home/vagrant/tmux-powerline/segments/{{ app }}.sh
    - source: salt://tmux/pid-segment.tmpl.sh
    - template: jinja
    - user: vagrant
    - context:
        component_name: {{ app }}
    - require:
      - cmd: dotfiles-install-tmux
      - git: tmux-powerline-install
{% endfor %}

# add tmux init commands to setup environment
tmux-ogre-init-conf:
  file.managed:
    - name: /home/vagrant/.tmux-ogre-init.conf
    - source: salt://dev-build/tmux-ogre-init.conf
    - user: vagrant
    - group: vagrant

tmux-ogre-init-conf-patch:
  file.append:
    - name: /home/vagrant/.tmux.conf
    - text: "\n# AUTOMATICALLY ADDED TMUX SALT CONFIG\nsource-file ~/.tmux-ogre-init.conf"
    - require:
      - cmd: dotfiles-install-tmux
