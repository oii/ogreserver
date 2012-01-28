from ogreserver import app, forms, celery

from flask import Flask, request, redirect, session, url_for, abort, render_template, flash
from flaskext.login import login_required, login_user, logout_user

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


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route("/home")
@login_required
def home():
    return "Home"


@app.route("/post", methods=['POST'])
def post():
    return "Done"

