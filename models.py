import uuid
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db, login_manager

ROLE_LABELS = {"CLUB": "Club Officer", "SSG": "SSG Officer", "SAS": "SAS Admin"}


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.String(32), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)
    role = db.Column(db.String(10), nullable=False, default="CLUB")
    organization_name = db.Column(db.String(120), nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    organized_events = db.relationship(
        "Event", backref="organizer", lazy=True,
        foreign_keys="Event.organizer_id",
    )

    def set_password(self, pw):  self.password_hash = generate_password_hash(pw)
    def check_password(self, pw):
        return bool(self.password_hash) and check_password_hash(self.password_hash, pw)

    @property
    def initials(self):
        parts = self.full_name.split()
        if not parts:
            return "?"
        return (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper()

    @property
    def role_label(self):
        return ROLE_LABELS.get(self.role, self.role)


class Event(db.Model):
    __tablename__ = "events"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    organizer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    venue = db.Column(db.String(200))
    event_date = db.Column(db.Date)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    target_audience = db.Column(db.String(200))
    status = db.Column(db.String(20), default="PENDING_SSG")
    remarks = db.Column(db.Text)
    qr_token = db.Column(db.String(64), unique=True, default=lambda: uuid.uuid4().hex)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    attendance_logs = db.relationship(
        "AttendanceLog", backref="event", cascade="all, delete-orphan", lazy=True
    )

    @property
    def status_label(self):
        return {
            "PENDING_SSG": "Pending SSG",
            "PENDING_SAS": "Pending SAS",
            "APPROVED": "Approved",
            "REJECTED": "Rejected",
        }.get(self.status, self.status)

    @property
    def status_color(self):
        return {
            "PENDING_SSG": "amber",
            "PENDING_SAS": "indigo",
            "APPROVED": "emerald",
            "REJECTED": "rose",
        }.get(self.status, "slate")

    @property
    def is_pending(self):
        return self.status in ("PENDING_SSG", "PENDING_SAS")


class AttendanceLog(db.Model):
    __tablename__ = "attendance_logs"
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    time_in = db.Column(db.DateTime, default=datetime.utcnow)
    time_out = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(10), default="PRESENT")
    verified_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    student = db.relationship("User", foreign_keys=[student_id])
    verifier = db.relationship("User", foreign_keys=[verified_by])

    __table_args__ = (
        db.UniqueConstraint("event_id", "student_id", name="uq_event_student"),
    )


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))