import uuid
from datetime import datetime, date, time, timedelta
from extensions import db
from models import User, Event, AttendanceLog


def init_db(app):
    with app.app_context():
        db.create_all()
        if User.query.count() == 0:
            seed_db()


def seed_db():
    """Populate realistic sample data on first run."""
    print("🌱 Seeding sample data…")

    # --- Users ---
    users = [
        User(school_id="ADMIN-001", full_name="Dr. Maria Santos",
             email="maria.santos@school.edu", role="SAS",
             organization_name="Student Affairs & Services"),
        User(school_id="SSG-001", full_name="Juan Cruz",
             email="juan.cruz@school.edu", role="SSG",
             organization_name="Supreme Student Government"),
        User(school_id="CLUB-001", full_name="Pedro Reyes",
             email="pedro.reyes@school.edu", role="CLUB",
             organization_name="Computer Science Society"),
        User(school_id="CLUB-002", full_name="Liza Mendoza",
             email="liza.mendoza@school.edu", role="CLUB",
             organization_name="Debate & Literary Club"),
        User(school_id="2024-0001", full_name="Ana Lopez",
             email="ana.lopez@school.edu", role="CLUB",
             organization_name="Computer Science Society"),
        User(school_id="2024-0002", full_name="Mark Villanueva",
             email="mark.villanueva@school.edu", role="CLUB",
             organization_name="Debate & Literary Club"),
        User(school_id="2024-0003", full_name="Sofia Reyes",
             email="sofia.reyes@school.edu", role="CLUB",
             organization_name="Computer Science Society"),
    ]
    for u in users:
        u.set_password("password123")
        db.session.add(u)
    db.session.commit()

    sas    = users[0]
    ssg    = users[1]
    club1  = users[2]
    club2  = users[3]
    students = users[4:]

    today = date.today()

    # --- Events ---
    events = [
        Event(
            title="Hackathon 2025: Code for Change",
            description="A 24-hour coding marathon for student innovators.",
            organizer_id=club1.id, venue="Main Auditorium",
            event_date=today + timedelta(days=10),
            start_time=time(8, 0), end_time=time(18, 0),
            target_audience="All CS & IT Students",
            status="APPROVED",
        ),
        Event(
            title="Annual Debate Championship",
            description="Inter-college debate tournament.",
            organizer_id=club2.id, venue="Gymnasium",
            event_date=today + timedelta(days=5),
            start_time=time(13, 0), end_time=time(17, 0),
            target_audience="All Students",
            status="APPROVED",
        ),
        Event(
            title="Leadership Summit 2025",
            description="Workshop on student leadership & governance.",
            organizer_id=ssg.id, venue="Function Hall",
            event_date=today - timedelta(days=7),
            start_time=time(9, 0), end_time=time(12, 0),
            target_audience="Officers & Representatives",
            status="APPROVED",
        ),
        Event(
            title="Science & Tech Fair",
            description="Exhibition of student science projects.",
            organizer_id=club1.id, venue="Covered Court",
            event_date=today - timedelta(days=20),
            start_time=time(8, 0), end_time=time(16, 0),
            target_audience="All Students",
            status="APPROVED",
        ),
        Event(
            title="Campus Clean-Up Drive",
            description="Environmental awareness activity.",
            organizer_id=ssg.id, venue="Campus Grounds",
            event_date=today + timedelta(days=3),
            start_time=time(6, 30), end_time=time(9, 0),
            target_audience="Volunteers",
            status="PENDING_SAS", remarks="SSG endorsed. Awaiting SAS final approval.",
        ),
        Event(
            title="Acoustic Night Fundraiser",
            description="Music night for charity.",
            organizer_id=club2.id, venue="Amphitheater",
            event_date=today + timedelta(days=15),
            start_time=time(18, 0), end_time=time(21, 0),
            target_audience="All Students",
            status="PENDING_SSG",
        ),
        Event(
            title="Esports Tournament",
            description="Mobile & PC gaming competition.",
            organizer_id=club1.id, venue="Computer Lab 3",
            event_date=today - timedelta(days=2),
            start_time=time(10, 0), end_time=time(17, 0),
            target_audience="Gamers",
            status="REJECTED", remarks="Venue conflict with scheduled exams.",
        ),
    ]
    db.session.add_all(events)
    db.session.commit()

    # --- Attendance logs ---
    def log(event, student, minutes_offset):
        base = datetime.combine(event.event_date, event.start_time) + timedelta(minutes=minutes_offset)
        status = "LATE" if minutes_offset > 15 else "PRESENT"
        db.session.add(AttendanceLog(
            event_id=event.id, student_id=student.id,
            time_in=base, status=status, verified_by=event.organizer_id,
        ))

    for ev in events[:4]:  # approved events
        for i, s in enumerate(students):
            log(ev, s, i * 4)

    db.session.commit()
    print(f"✅ Seeded {len(users)} users, {len(events)} events, "
          f"{AttendanceLog.query.count()} attendance records.")
    print("   Demo logins  →  ADMIN-001 / SSG-001 / CLUB-001  (password: password123)")