from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, abort)
from flask_login import login_required, current_user
from extensions import db
from models import Event
from utils.decorators import role_required

bp = Blueprint("approvals", __name__)


def _visible_query():
    """Events this role is allowed to act upon."""
    if current_user.role == "SSG":
        return Event.query.filter_by(status="PENDING_SSG")
    if current_user.role == "SAS":
        return Event.query.filter_by(status="PENDING_SAS")
    return Event.query.filter(False)


@bp.route("/")
@login_required
@role_required("SSG", "SAS")
def index():
    filter_tab = request.args.get("tab", "pending")

    all_q = Event.query
    if current_user.role == "SSG":
        all_q = all_q.filter(Event.status.in_(["PENDING_SSG", "PENDING_SAS", "REJECTED"]))
    else:
        all_q = all_q.filter(Event.status.in_(["PENDING_SAS", "APPROVED", "REJECTED"]))

    if filter_tab == "pending":
        q = _visible_query().order_by(Event.created_at.desc()).all()
    elif filter_tab == "approved":
        q = all_q.filter_by(status="APPROVED").order_by(Event.event_date.desc()).all()
    elif filter_tab == "rejected":
        q = all_q.filter_by(status="REJECTED").order_by(Event.event_date.desc()).all()
    else:
        q = all_q.order_by(Event.created_at.desc()).all()

    counts = {
        "pending":  _visible_query().count(),
        "approved": all_q.filter_by(status="APPROVED").count(),
        "rejected": all_q.filter_by(status="REJECTED").count(),
        "all":      all_q.count(),
    }

    return render_template("approvals.html", events=q, tab=filter_tab, counts=counts)


@bp.route("/<int:event_id>/approve", methods=["POST"])
@login_required
@role_required("SSG", "SAS")
def approve(event_id):
    ev = db.session.get(Event, event_id) or abort(404)
    remarks = request.form.get("remarks", "").strip()

    if current_user.role == "SSG" and ev.status == "PENDING_SSG":
        ev.status = "PENDING_SAS"
        ev.remarks = remarks or "Endorsed by SSG."
        flash(f"“{ev.title}” endorsed to SAS for final approval.", "success")
    elif current_user.role == "SAS" and ev.status == "PENDING_SAS":
        ev.status = "APPROVED"
        ev.remarks = remarks or "Approved by SAS."
        flash(f"“{ev.title}” has been APPROVED.", "success")
    else:
        flash("This event is not awaiting your approval.", "warning")
    db.session.commit()
    return redirect(url_for("approvals.index"))


@bp.route("/<int:event_id>/reject", methods=["POST"])
@login_required
@role_required("SSG", "SAS")
def reject(event_id):
    ev = db.session.get(Event, event_id) or abort(404)
    remarks = request.form.get("remarks", "").strip() or "No reason provided."
    ev.status = "REJECTED"
    ev.remarks = remarks
    db.session.commit()
    flash(f"“{ev.title}” was rejected.", "info")
    return redirect(url_for("approvals.index"))