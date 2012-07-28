from ogreserver import app, tasks, json, uploads

from ogreserver.forms.auth import LoginForm
from ogreserver.forms.search import SearchForm

from ogreserver.models.user import User
from ogreserver.models.datastore import DataStore
from ogreserver.models.reputation import Reputation
from ogreserver.models.log import Log

from ogreserver.tasks import store_ebook

from flask import Flask, request, redirect, session, url_for, abort, render_template, flash
from flask.ext.login import login_required, login_user, logout_user, current_user


@app.route("/")
@login_required
def index():
    return redirect(url_for("home"))


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        login_user(form.user)
        session['user_id'] = form.user.id
        return redirect(request.args.get("next") or url_for("index"))
    return render_template("login.html", form=form)


@app.route("/auth", methods=['POST'])
def auth():
    user = User.authenticate(username=request.form.get("username"), password=request.form.get("password"))
    if not user:
        return "0"
    else:
        return user.assign_auth_key()


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route("/home")
@login_required
def home():
    return dedrm()


@app.route("/list")
@login_required
def list(searchtext=None):
    form = SearchForm(request.args)

    ds = DataStore(current_user)
    rs = ds.list()
    return render_template("list.html", ebooks=rs)


@app.route("/search", methods=['GET', 'POST'])
@login_required
def search():
    print dir(request)

    # TODO handle normal for post; feed list()
    if request.method == "POST":
        return list(form.searchtext)
    return render_template("search.html", form=form)


@app.route("/view")
@login_required
def view(sdbkey=None):
    ds = DataStore(current_user)
    rs = ds.list()
    return render_template("view.html", ebooks=rs)


@app.route("/dedrm")
@login_required
def dedrm():
    return render_template("dedrm.html")


@app.route("/kill")
def kill():
    import boto
    sdb = boto.connect_sdb(app.config['AWS_ACCESS_KEY'], app.config['AWS_SECRET_KEY'])
    sdb.delete_domain("ogre_books")
    sdb.delete_domain("ogre_formats")
    sdb.delete_domain("ogre_versions")
    sdb.create_domain("ogre_books")
    sdb.create_domain("ogre_formats")
    sdb.create_domain("ogre_versions")
    return "Killed"


@app.route("/show")
def show():
    import boto
    sdb = boto.connect_sdb(app.config['AWS_ACCESS_KEY'], app.config['AWS_SECRET_KEY'])

    out = ""
    rs = sdb.select("ogre_books", "select * from ogre_books")
    for item in rs:
        out += str(item) + "\n"

    out += "\n"
    rs = sdb.select("ogre_formats", "select * from ogre_formats")
    for item in rs:
        out += str(item) + "\n"

    out += "\n"
    rs = sdb.select("ogre_versions", "select * from ogre_versions")
    for item in rs:
        out += str(item) + "\n"

    return out


@app.route("/post", methods=['POST'])
def post():
    try:
        # authenticate user
        user = User.validate_auth_key(
            username=request.form.get("username"),
            api_key=request.form.get("api_key")
        )
        if user is None:
            return "API Auth Failed: Post"

        # decode the json payload
        data = json.loads(request.form.get("ebooks"))

    except KeyError:
        return "Bad Request"

    # stats log the upload
    Log.create(user.id, "CONNECT", request.form.get("total"), request.form.get("api_key"))

    # update the library
    ds = DataStore(user)
    new_ebook_count = ds.update_library(data)
    Log.create(user.id, "NEW", new_ebook_count, request.form.get("api_key"))

    # handle badge and reputation changes
    r = Reputation(user)
    r.new_ebooks(new_ebook_count)
    r.earn_badges()
    msgs = r.get_new_badges()

    # query books missing from S3 and supply back to the client
    rs = ds.find_missing_books()
    return json.dumps({
        'ebooks_to_upload': rs,
        'messages': msgs
    })


@app.route("/upload", methods=['POST'])
def upload():
    user = User.validate_auth_key(
        username=request.form.get("username"),
        api_key=request.form.get("api_key")
    )
    if user is None:
        return "API Auth Failed: Upload"

    # stats log the upload
    Log.create(user.id, "UPLOAD", 1, request.form.get("api_key"))

    uploads.save(request.files['ebook'], None, "%s%s" % (request.form.get("filehash"), request.form.get("format")))
    res = store_ebook.apply_async((user.id, request.form.get("sdbkey"), request.form.get("filehash"), request.form.get("format")))
    return res.task_id


@app.route("/result/<task_id>")
def show_result(task_id):
    retval = store_ebook.AsyncResult(task_id).get(timeout=1.0)
    return repr(retval)

