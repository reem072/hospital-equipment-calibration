from functools import wraps
from urllib.parse import urlsplit

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from extensions import db, login_manager
from models import ActivityLog, User

auth_bp = Blueprint("auth", __name__)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        from flask import abort
        if not current_user.is_authenticated or current_user.role != "Admin":
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def log_action(action, equipment_identifier=""):
    username = current_user.username if current_user.is_authenticated else "system"
    user_id = current_user.id if current_user.is_authenticated else None
    db.session.add(ActivityLog(username=username, user_id=user_id, action=action, equipment_identifier=equipment_identifier))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        identity = request.form.get("identity", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter(db.or_(db.func.lower(User.username) == identity, db.func.lower(User.email) == identity)).first()
        if user and user.active and user.check_password(password):
            login_user(user, remember=request.form.get("remember") == "on")
            log_action("Logged in")
            db.session.commit()
            next_url = request.args.get("next", "")
            parsed_next = urlsplit(next_url)
            if next_url.startswith("/") and not next_url.startswith("//") and not parsed_next.scheme and not parsed_next.netloc:
                return redirect(next_url)
            return redirect(url_for("dashboard"))
        flash("The username/email or password was not recognized.", "danger")
    return render_template("login.html")


@auth_bp.post("/logout")
def logout():
    if current_user.is_authenticated:
        log_action("Logged out")
        db.session.commit()
    logout_user()
    return redirect(url_for("auth.login"))