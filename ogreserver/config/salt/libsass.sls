{% set sass_version = pillar.get('sass_version', '3.3.6') %}

libsass-src:
  git.latest:
    - name: https://github.com/sass/libsass.git
    - rev: {{ sass_version }}
    - target: /tmp/libsass
    - unless: test -f /usr/local/bin/sassc

sassc:
  git.latest:
    - name: https://github.com/sass/sassc.git
    - rev: {{ sass_version }}
    - target: /tmp/sassc
    - unless: test -f /usr/local/bin/sassc
  cmd.wait:
    - name: SASS_LIBSASS_PATH=/tmp/libsass make
    - cwd: /tmp/sassc
    - require:
      - git: libsass-src
    - watch:
      - git: sassc

sassc-install:
  cmd.run:
    - name: cp /tmp/sassc/bin/sassc /usr/local/bin/sassc && chmod 755 /usr/local/bin/sassc
    - unless: test -f /usr/local/bin/sassc
    - require:
      - cmd: sassc
