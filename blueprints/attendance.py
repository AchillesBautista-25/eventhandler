from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Event, AttendanceLog, User

bp = Blueprint("attendance", __name__)


@bp.route("/checkin", methods=["POST"])
@login_required
def checkin():
    data = request.get_json(silent=True) or request.form
    event_id  = data.get("event_id")
    school_id = (data.get("school_id") or "").strip()

    event = db.session.get(Event, int(event_id)) if event_id else None
    if not event or event.status != "APPROVED":
        return jsonify(ok=False, message="Event not available."), 400

    student = User.query.filter_by(school_id=school_id).first()
    if not student:
        return jsonify(ok=False, message=f"Unknown Student ID: {school_id}"), 404

    existing = AttendanceLog.query.filter_by(
        event_id=event.id, student_id=student.id
    ).first()
    if existing:
        return jsonify(
            ok=False,
            message=f"{student.full_name} is already checked in at "
                    f"{existing.time_in.strftime('%I:%M %p')}.",
        ), 409

    # Late if >15 min after event start
    now = datetime.now()
    start_dt = datetime.combine(event.event_date, event.start_time)
    status = "LATE" if now > start_dt + timedelta(minutes=15) else "PRESENT"

    log = AttendanceLog(
        event_id=event.id,
        student_id=student.id,
        time_in=now,
        status=status,
        verified_by=current_user.id,
    )
    db.session.add(log)
    db.session.commit()

    return jsonify(
        ok=True,
        message=f"{student.full_name} — {status}",
        student={
            "name": student.full_name,
            "school_id": student.school_id,
            "time_in": now.strftime("%I:%M %p"),
            "status": status,
        },
    )