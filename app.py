from flask import Flask, render_template, redirect, url_for, flash
from flask_login import current_user
from config import Config
from extensions import db, login_manager, oauth
from database import init_db
from utils.helpers import qr_data_url


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    oauth.init_app(app)

    # Register Google provider only if credentials are present
    if app.config["GOOGLE_CLIENT_ID"] and app.config["GOOGLE_CLIENT_SECRET"]:
        oauth.register(
            name="google",
            client_id=app.config["GOOGLE_CLIENT_ID"],
            client_secret=app.config["GOOGLE_CLIENT_SECRET"],
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )

    # Blueprints
    from blueprints.auth       import bp as auth_bp
    from blueprints.dashboard  import bp as dash_bp
    from blueprints.events     import bp as events_bp
    from blueprints.approvals  import bp as approvals_bp
    from blueprints.attendance import bp as attendance_bp
    from blueprints.reports    import bp as reports_bp
    from blueprints.settings   import bp as settings_bp

    app.register_blueprint(auth_bp,       url_prefix="/auth")
    app.register_blueprint(dash_bp,       url_prefix="")
    app.register_blueprint(events_bp,     url_prefix="/events")
    app.register_blueprint(approvals_bp,  url_prefix="/approvals")
    app.register_blueprint(attendance_bp, url_prefix="/attendance")
    app.register_blueprint(reports_bp,    url_prefix="/reports")
    app.register_blueprint(settings_bp,   url_prefix="/settings")

    # Template helpers
    app.jinja_env.filters["qr"] = qr_data_url

    @app.context_processor
    def inject_globals():
        return {
            "RoleLabels": {"CLUB": "Club Officer", "SSG": "SSG Officer", "SAS": "SAS Admin"},
        }

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors.html", code=403,
                               message="You don't have permission to access this page."), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors.html", code=404,
                               message="The page you're looking for doesn't exist."), 404

    return app


app = create_app()
init_db(app)

if __name__ == "__main__":
    init_db(app)
    app.run(host="0.0.0.0", port=app.config["PORT"], debug=True)