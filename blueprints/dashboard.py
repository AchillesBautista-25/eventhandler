from datetime import date, datetime, timedelta

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import func

from extensions import db
from models import User, Event, AttendanceLog

bp = Blueprint("dashboard", __name__)


@bp.route("/")
def index():
    """Landing route — send everyone somewhere sensible."""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.home"))
    return redirect(url_for("auth.login"))


@bp.route("/dashboard")
@login_required
def home():
    today = date.today()

    # --- KPI: registered students ---
    total_students = User.query.filter_by(role="CLUB").count()

    # --- KPI: active attendees in last 30 days ---
    active_attendees = (
        db.session.query(func.count(func.distinct(AttendanceLog.student_id)))
        .filter(AttendanceLog.time_in >= datetime.utcnow() - timedelta(days=30))
        .scalar()
        or 0
    )

    # --- KPI: pending approvals (role-aware) ---
    pending_q = Event.query.filter_by(status="PENDING_SSG")
    if current_user.role == "SAS":
        pending_q = Event.query.filter_by(status="PENDING_SAS")
    elif current_user.role == "CLUB":
        pending_q = Event.query.filter_by(
            organizer_id=current_user.id, status="PENDING_SSG"
        )
    pending_count = pending_q.count()

    # --- Upcoming approved events ---
    upcoming = (
        Event.query
        .filter(Event.status == "APPROVED", Event.event_date >= today)
        .order_by(Event.event_date)
        .limit(6)
        .all()
    )

    # --- Completed events ---
    completed_count = Event.query.filter(
        Event.status == "APPROVED", Event.event_date < today
    ).count()

    # --- Attendance rate (%) ---
    approved_total = Event.query.filter_by(status="APPROVED").count() or 1
    total_attendance = AttendanceLog.query.count()
    attendance_rate = round(
        (total_attendance / (approved_total * max(total_students, 1))) * 100, 1
    )
    if attendance_rate > 100:
        attendance_rate = 100.0

    # --- Chart data: last 6 approved events ---
    recent_events = (
        Event.query
        .filter(Event.status == "APPROVED")
        .order_by(Event.event_date.desc())
        .limit(6)
        .all()
    )[::-1]  # reverse so oldest → newest

    chart_labels = [
        e.event_date.strftime("%b %d") if e.event_date else "—"
        for e in recent_events
    ]
    chart_values = [len(e.attendance_logs) for e in recent_events]

    # --- Recent activity ---
    recent_logs = (
        AttendanceLog.query
        .order_by(AttendanceLog.time_in.desc())
        .limit(8)
        .all()
    )

    return render_template(
        "dashboard.html",
        total_students=total_students,
        active_attendees=active_attendees,
        pending_count=pending_count,
        upcoming=upcoming,
        completed_count=completed_count,
        attendance_rate=attendance_rate,
        chart_labels=chart_labels,
        chart_values=chart_values,
        recent_logs=recent_logs,
        today=today,
    )