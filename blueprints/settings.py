from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, abort)
from flask_login import login_required, current_user
from extensions import db
from models import User
from utils.decorators import role_required

bp = Blueprint("settings", __name__)


@bp.route("/")
@login_required
def index():
    users = None
    if current_user.role == "SAS":
        users = User.query.order_by(User.created_at.desc()).all()
    return render_template("settings.html", users=users)


@bp.route("/profile", methods=["POST"])
@login_required
def update_profile():
    current_user.full_name = request.form.get("full_name", current_user.full_name).strip()
    current_user.email     = request.form.get("email", current_user.email).strip()
    current_user.organization_name = request.form.get("organization_name", "").strip() or None
    db.session.commit()
    flash("Profile updated.", "success")
    return redirect(url_for("settings.index"))


@bp.route("/password", methods=["POST"])
@login_required
def update_password():
    current = request.form.get("current_password", "")
    new     = request.form.get("new_password", "")
    if not current_user.check_password(current):
        flash("Current password is incorrect.", "error")
    elif len(new) < 6:
        flash("New password must be at least 6 characters.", "error")
    else:
        current_user.set_password(new)
        db.session.commit()
        flash("Password updated.", "success")
    return redirect(url_for("settings.index"))


@bp.route("/users/<int:user_id>/role", methods=["POST"])
@login_required
@role_required("SAS")
def change_role(user_id):
    user = db.session.get(User, user_id) or abort(404)
    new_role = request.form.get("role")
    if new_role not in ("CLUB", "SSG", "SAS"):
        abort(400)
    user.role = new_role
    db.session.commit()
    flash(f"{user.full_name} is now {new_role}.", "success")
    return redirect(url_for("settings.index"))