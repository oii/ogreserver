include:
  - debian-repos.backports

redis-server:
  pkg.installed:
    - fromrepo: {{ grains['oscodename'] }}-backports
    - require:
      - pkgrepo: backports-pkgrepo
  service.running:
    - name: redis
    - require:
      - pkg: redis-server
