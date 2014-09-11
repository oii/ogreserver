from __future__ import absolute_import

from .factory import create_app, configure_extensions, register_blueprints

app = create_app()
configure_extensions(app)
register_blueprints(app)
