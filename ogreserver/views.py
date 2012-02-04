from ogreserver import app, forms, tasks, json, uploads

from ogreserver.models.user import User
from ogreserver.models.datastore import DataStore

from ogreserver.tasks import store_ebook

from flask import Flask, request, redirect, session, url_for, abort, render_template, flash
from flask.ext.login import login_required, login_user, logout_user


@app.route("/")
@login_required
def index():
    return redirect(url_for("home"))


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = forms.LoginForm()
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


@app.route("/dedrm")
@login_required
def dedrm():
    return render_template("dedrm.html")


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

        ebooks_json = request.form.get("ebooks")

    except KeyError:
        return "Bad Request"

    # update the library
    ds = DataStore(user)
    ds.update_library(json.loads(ebooks_json))

    # send to the client the list of books they need to upload
    rs = ds.find_missing_books()
    return json.dumps(rs)


@app.route("/upload", methods=['POST'])
def upload():
    user = User.validate_auth_key(
        username=request.form.get("username"),
        api_key=request.form.get("api_key")
    )
    if user is None:
        return "API Auth Failed: Upload"

    fname = uploads.save(request.files['ebook'], None, request.form.get("filehash"))
    res = store_ebook.apply_async((request.form.get("sdbkey"), request.form.get("filehash")))
    return res.task_id


@app.route("/result/<task_id>")
def show_result(task_id):
    retval = store_ebook.AsyncResult(task_id).get(timeout=1.0)
    return repr(retval)

