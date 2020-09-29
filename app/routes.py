from flask import flash
from flask import jsonify
import os
from array import *
from werkzeug.utils import secure_filename
from flask import make_response, redirect
from flask import render_template, session, request
from flask import url_for

from app import ALLOWED_EXTENSIONS
from app.forms import LoginForm
from app import app

from app.models import upload_data_from_db
from app.models import Rate, Service, PayPeriod, Address


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1] in ALLOWED_EXTENSIONS


def init_user():
    session["auth"] = {"login": False, "user_name": "", "user_mail": "", "admin": False}


def set_user_session(name, mail):
    session["auth"] = {"login": True, "user_name": name, "user_mail": mail}


@app.route("/")
def render_index():
    if session.get("auth") is None:
        init_user()

    return render_template("index.html")


@app.route("/import_file", methods=["GET", "POST"])
def render_import_file():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)

        file = request.files["file"]

        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            # filename = secure_filename(file.filename)
            file.save(
                    os.path.join(app.config["UPLOAD_FOLDER"], app.config["FILENAME_IMPORT"])
                    )
            flash("Файл загружен")
            upload_data_from_db()
            return redirect(url_for("render_index"))

    return render_template("import_file.html")


@app.route("/signin", methods=["POST", "GET"])
def render_signin():
    form = LoginForm()
    if request.method == "POST":
        set_user_session(name="user.name", mail="user.mail")
        if form.mail.data == "admin@admin":
            session["auth"]["admin"] = True

        return redirect(url_for("render_index"))

    return render_template("signin.html", form=form)


@app.route("/rate")
def render_rate():
    rates = []
    for rs in Rate.query.distinct(Rate.id_service).group_by(Rate.id_service):
        srv = dict()
        addr = ""
        s = Service.query.filter_by(id=rs.id_service).first()
        srv["service_name"] = s.name_ru
        addr_sum = []
        for r in (
                Rate.query.filter_by(id_service=rs.id_service)
                        .order_by(Rate.id_address.desc())
                        .distinct(Rate.id_address)
        ):
            if not r.id_address == addr:
                addr = r.id_address

                a = Address.query.filter_by(id=r.id_address).first()
                bulk = ""
                if len(a.bulk)>0:
                    bulk = ", корп." + a.bulk

                addr_sum.append(
                        {
                            "sum"    : r.sum,
                            "address": "г.Астрахань, "
                                       + a.street_ru
                                       + ", д."
                                       + a.home
                                       + bulk,
                            }
                        )

        srv["addr_sum"] = addr_sum
        rates.append(srv)

    return render_template("rate.html", rates=rates)


@app.route("/signout")
def render_signout():
    init_user()
    return redirect(url_for("render_index"))


@app.route("/account")
def render_account():
    if not session["auth"]["login"]:
        return redirect(url_for("render_signin"))
