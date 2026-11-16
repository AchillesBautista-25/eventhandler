import csv, io
from datetime import datetime
from flask import (Blueprint, render_template, request, Response,
                   send_file)
from flask_login import login_required
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from extensions import db
from models import Event, AttendanceLog, User
from utils.decorators import role_required

bp = Blueprint("reports", __name__)


def _filtered_logs():
    q = (AttendanceLog.query
         .join(Event, AttendanceLog.event_id == Event.id)
         .join(User, AttendanceLog.student_id == User.id))

    event_id = request.args.get("event_id")
    org      = request.args.get("organization")
    date_from = request.args.get("date_from")
    date_to   = request.args.get("date_to")

    if event_id:
        q = q.filter(Event.id == int(event_id))
    if org:
        q = q.filter(Event.organizer_id == int(org))
    if date_from:
        q = q.filter(Event.event_date >= datetime.strptime(date_from, "%Y-%m-%d").date())
    if date_to:
        q = q.filter(Event.event_date <= datetime.strptime(date_to, "%Y-%m-%d").date())

    return q.order_by(AttendanceLog.time_in.desc())


@bp.route("/")
@login_required
@role_required("SSG", "SAS")
def index():
    logs    = _filtered_logs().limit(500).all()
    events  = Event.query.filter_by(status="APPROVED").order_by(Event.event_date.desc()).all()
    orgs    = (User.query.filter(User.role.in_(["CLUB", "SSG"]))
               .order_by(User.organization_name).all())

    # Summary by event
    summary = []
    for ev in events:
        total = len(ev.attendance_logs)
        late  = sum(1 for l in ev.attendance_logs if l.status == "LATE")
        summary.append({
            "event": ev, "total": total, "late": late,
            "present": total - late,
        })

    return render_template(
        "reports.html",
        logs=logs, events=events, orgs=orgs, summary=summary,
    )


@bp.route("/export.csv")
@login_required
@role_required("SSG", "SAS")
def export_csv():
    logs = _filtered_logs().all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Event", "Event Date", "Venue", "Student ID",
                     "Student Name", "Organization", "Time In",
                     "Time Out", "Status"])
    for l in logs:
        writer.writerow([
            l.event.title,
            l.event.event_date.strftime("%Y-%m-%d") if l.event.event_date else "",
            l.event.venue or "",
            l.student.school_id,
            l.student.full_name,
            l.student.organization_name or "",
            l.time_in.strftime("%Y-%m-%d %H:%M") if l.time_in else "",
            l.time_out.strftime("%Y-%m-%d %H:%M") if l.time_out else "",
            l.status,
        ])
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=attendance_report.csv"},
    )


@bp.route("/export.xlsx")
@login_required
@role_required("SSG", "SAS")
def export_xlsx():
    logs = _filtered_logs().all()
    wb = Workbook()
    ws = wb.active
    ws.title = "Attendance"

    headers = ["Event", "Event Date", "Venue", "Student ID",
               "Student Name", "Organization", "Time In", "Time Out", "Status"]
    ws.append(headers)
    header_fill = PatternFill("solid", fgColor="3B49DF")
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = header_fill

    for l in logs:
        ws.append([
            l.event.title,
            l.event.event_date.strftime("%Y-%m-%d") if l.event.event_date else "",
            l.event.venue or "",
            l.student.school_id,
            l.student.full_name,
            l.student.organization_name or "",
            l.time_in.strftime("%Y-%m-%d %H:%M") if l.time_in else "",
            l.time_out.strftime("%Y-%m-%d %H:%M") if l.time_out else "",
            l.status,
        ])

    for i, _ in enumerate(headers, 1):
        ws.column_dimensions[chr(64 + i)].width = 22

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(
        buf,
        as_attachment=True,
        download_name="attendance_report.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )