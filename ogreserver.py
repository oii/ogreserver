from ogreserver import app
app.wsgi_app = ProxyFix(app.wsgi_app)
