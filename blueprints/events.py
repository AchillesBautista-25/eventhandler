from datetime import datetime, date, time
from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, abort, jsonify)
from flask_login import login_required, current_user
from extensions import db
from models import Event, AttendanceLog
from utils.decorators import role_required

bp = Blueprint("events", __name__)


@bp.route("/")
@login_required
def list_events():
    status_filter = request.args.get("status", "APPROVED")
    q = Event.query
    if status_filter != "ALL":
        q = q.filter_by(status=status_filter)

    if current_user.role == "CLUB":
        # Show events the user can attend (all approved) + their own proposals
        events = (Event.query
                  .filter((Event.status == "APPROVED") |
                          (Event.organizer_id == current_user.id))
                  .order_by(Event.event_date.desc()).all())
    else:
        events = q.order_by(Event.event_date.desc()).all()

    return render_template("events.html", events=events, status_filter=status_filter)


@bp.route("/new", methods=["POST"])
@login_required
@role_required("CLUB", "SSG", "SAS")
def create_event():
    try:
        ev = Event(
            title=request.form["title"].strip(),
            description=request.form.get("description", "").strip(),
            organizer_id=current_user.id,
            venue=request.form.get("venue", "").strip(),
            event_date=datetime.strptime(request.form["event_date"], "%Y-%m-%d").date(),
            start_time=datetime.strptime(request.form["start_time"], "%H:%M").time(),
            end_time=datetime.strptime(request.form["end_time"], "%H:%M").time(),
            target_audience=request.form.get("target_audience", "").strip(),
            status="PENDING_SSG",
        )
        db.session.add(ev)
        db.session.commit()
        flash(f"Proposal “{ev.title}” submitted for SSG review.", "success")
    except (KeyError, ValueError) as exc:
        flash(f"Invalid form submission: {exc}", "error")
    return redirect(url_for("events.list_events"))


@bp.route("/<int:event_id>/scanner")
@login_required
def scanner(event_id):
    ev = db.session.get(Event, event_id) or abort(404)
    if ev.status != "APPROVED":
        flash("Only approved events can accept attendance.", "warning")
        return redirect(url_for("events.list_events"))
    return render_template("scanner.html", event=ev,
                           logs=ev.attendance_logs)