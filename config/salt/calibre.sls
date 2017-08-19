calibre-install:
  archive.extracted:
    - name: /opt/calibre
    - source: https://s3-eu-west-1.amazonaws.com/calibre-binary-mirror/calibre-3.6.0-x86_64.txz
    - source_hash: sha1=c14765495a4d58da7fc35e5f3eefcedaa7cfee59
    - archive_format: tar

/opt/calibre/calibre_postinstall; true:
  cmd.run:
    - onchanges:
      - archive: calibre-install

# required packages for ebook-meta & ebook-convert
calibre-pkgs:
  pkg.installed:
    - names:
      - libltdl7
      - python-pyqt5
