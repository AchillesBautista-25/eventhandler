from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, current_app)
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db, oauth
from models import User

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))

    if request.method == "POST":
        school_id = (request.form.get("school_id") or "").strip()
        password  = request.form.get("password") or ""
        # role tab is cosmetic; real role is validated from DB
        user = User.query.filter_by(school_id=school_id).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            flash(f"Welcome back, {user.full_name.split()[0]}!", "success")
            return redirect(url_for("dashboard.home"))
        flash("Invalid School ID or password.", "error")

    return render_template("login.html")


@bp.route("/google")
def google_login():
    if not current_app.config["GOOGLE_CLIENT_ID"]:
        flash("Google OAuth is not configured on this server.", "warning")
        return redirect(url_for("auth.login"))
    redirect_uri = url_for("auth.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@bp.route("/callback")
def google_callback():
    try:
        token = oauth.google.authorize_access_token()
        info = token.get("userinfo") or oauth.google.parse_id_token(token)
        email = info.get("email", "").lower()
        name  = info.get("name") or email.split("@")[0]
        avatar = info.get("picture")

        user = User.query.filter_by(email=email).first()
        if not user:
            # First time OAuth sign-in — create a CLUB-role account
            sid = "G-" + email.split("@")[0][:16]
            user = User(
                school_id=sid,
                full_name=name,
                email=email,
                role="CLUB",
                avatar_url=avatar,
            )
            user.set_password(None)
            db.session.add(user)
            db.session.commit()
        else:
            if avatar:
                user.avatar_url = avatar
                db.session.commit()

        login_user(user, remember=True)
        flash(f"Welcome, {user.full_name.split()[0]}!", "success")
        return redirect(url_for("dashboard.home"))
    except Exception as exc:  # pragma: no cover
        current_app.logger.exception("Google OAuth failed")
        flash(f"Google sign-in failed: {exc}", "error")
        return redirect(url_for("auth.login"))


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))