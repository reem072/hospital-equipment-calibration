import os
from datetime import datetime
from datetime import date, timedelta
from pathlib import Path

from flask import Flask, render_template, request, flash, redirect, url_for, abort
from flask_login import current_user, login_required

from extensions import csrf, db, login_manager
from models import ActivityLog, CalibrationRecord, Equipment, Technician, User

BASE_DIR = Path(__file__).resolve().parent


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "college-prototype-change-this-key"),
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{(BASE_DIR / 'database' / 'calibration.db').as_posix()}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        REMEMBER_COOKIE_HTTPONLY=True,
    )
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    (BASE_DIR / "database").mkdir(exist_ok=True)
    (BASE_DIR / "static" / "qrcodes").mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    from auth import auth_bp
    from calibration import calibration_bp
    from equipment import equipment_bp
    from qr_routes import qr_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(equipment_bp)
    app.register_blueprint(calibration_bp)
    app.register_blueprint(qr_bp)

    @app.context_processor
    def inject_sidebar_counts():
        today = date.today()
        return {"sidebar_overdue_count": Equipment.query.filter(Equipment.next_calibration_due < today).count(),
            "today_date": today.strftime("%d %b %Y"), "now_hour": datetime.now().hour}

    @app.get("/")
    @login_required
    def dashboard():
        today = date.today()
        soon = today + timedelta(days=30)
        equipment = Equipment.query.order_by(Equipment.name).all()
        records = CalibrationRecord.query.order_by(CalibrationRecord.created_at.desc()).limit(6).all()
        due_soon = Equipment.query.filter(Equipment.next_calibration_due >= today, Equipment.next_calibration_due <= soon).order_by(Equipment.next_calibration_due).all()
        due_week = Equipment.query.filter(Equipment.next_calibration_due >= today, Equipment.next_calibration_due <= today + timedelta(days=7)).order_by(Equipment.next_calibration_due).all()
        overdue = Equipment.query.filter(Equipment.next_calibration_due < today).order_by(Equipment.next_calibration_due).all()
        status_counts = {status: sum(item.calibration_status == status for item in equipment) for status in ("VALID", "DUE SOON", "OVERDUE", "FAILED", "ADJUSTMENT REQUIRED", "UNDER MAINTENANCE", "NOT SCHEDULED")}
        categories = {}
        for item in equipment:
            categories[item.category] = categories.get(item.category, 0) + 1
        return render_template("dashboard.html", equipment=equipment, records=records, due_soon=due_soon, due_week=due_week, overdue=overdue,
                               total=len(equipment), calibrated=sum(item.last_calibration_date is not None for item in equipment),
                               maintenance=status_counts["UNDER MAINTENANCE"], status_counts=status_counts, categories=categories)

    @app.get("/technicians")
    @login_required
    def technicians():
        technician_rows = Technician.query.order_by(Technician.name).all()
        return render_template("technicians.html", technicians=technician_rows)

    @app.post("/technicians/add")
    @login_required
    def add_technician():
        if current_user.role != "Admin":
            abort(403)
        name = request.form.get("name", "").strip()
        employee_id = request.form.get("employee_id", "").strip()
        department = request.form.get("department", "").strip()
        email = request.form.get("email", "").strip().lower()
        if not all((name, employee_id, department, email)):
            flash("Name, employee ID, department, and email are required.", "danger")
        elif Technician.query.filter((Technician.employee_id == employee_id) | (Technician.email == email)).first():
            flash("Employee ID or email is already registered.", "danger")
        else:
            db.session.add(Technician(name=name, employee_id=employee_id, department=department, email=email,
                                      phone=request.form.get("phone", "").strip(), role=request.form.get("role", "Biomedical Engineer/Technician").strip()))
            db.session.commit()
            flash("Technician added.", "success")
        return redirect(url_for("technicians"))

    @app.get("/reports")
    @login_required
    def reports():
        report_type = request.args.get("type", "equipment")
        technician_id = request.args.get("technician_id", type=int)
        records_query = CalibrationRecord.query
        if report_type == "technician" and technician_id:
            records_query = records_query.filter_by(technician_id=technician_id)
        records = records_query.order_by(CalibrationRecord.calibration_date.desc()).all()
        return render_template("reports.html", equipment=Equipment.query.order_by(Equipment.department, Equipment.name).all(),
                               records=records, report_type=report_type, report_technicians=Technician.query.order_by(Technician.name).all(),
                               selected_technician_id=technician_id)

    @app.get("/privacy")
    @login_required
    def privacy():
        return render_template("privacy.html")

    @app.get("/settings")
    @login_required
    def settings():
        return render_template("settings.html")

    @app.get("/activity")
    @login_required
    def activity():
        logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(100).all()
        return render_template("activity.html", logs=logs)

    with app.app_context():
        db.create_all()
        seed_demo_data()
    app.jinja_env.globals["getattr"] = getattr

    return app


def seed_demo_data():
    if User.query.filter_by(username="admin").first():
        return
    demo_technicians = [
        Technician(name="Amina Hassan", employee_id="BIO-001", department="Biomedical Engineering", email="amina@example.test", phone="555-0101"),
        Technician(name="Omar Farouk", employee_id="BIO-002", department="Biomedical Engineering", email="omar@example.test", phone="555-0102"),
    ]
    db.session.add_all(demo_technicians)
    db.session.flush()
    admin = User(username="admin", email="admin@example.test", role="Admin")
    admin.set_password("Admin123!")
    technician_user = User(username="technician", email="tech@example.test", role="Technician")
    technician_user.set_password("Tech123!")
    db.session.add_all([admin, technician_user])
    today = date.today()
    demo_items = [
        ("ECG-001", "ECG Machine", "Diagnostic", "Philips", "PageWriter TC20", "ECG-26001", "ICU", "ICU Bay 2", 45, "Active", demo_technicians[0]),
        ("PM-001", "Patient Monitor", "Monitoring", "Mindray", "BeneVision N12", "PM-26001", "ICU", "ICU Bay 4", 180, "Active", demo_technicians[0]),
        ("IP-001", "Infusion Pump", "Infusion", "B. Braun", "Infusomat Space", "IP-26001", "Surgical Ward", "Ward 3 Store", -12, "Active", demo_technicians[1]),
        ("DEF-001", "Defibrillator", "Emergency", "Zoll", "R Series", "DEF-26001", "Emergency", "Resuscitation Room", 320, "Active", demo_technicians[1]),
        ("VENT-001", "Ventilator", "Respiratory", "Drager", "Evita V600", "VENT-26001", "ICU", "ICU Bay 1", 75, "Under Maintenance", demo_technicians[0]),
    ]
    equipment_rows = []
    for equipment_id, name, category, manufacturer, model, serial, department, location, due_days, status, technician in demo_items:
        equipment_rows.append(Equipment(equipment_id=equipment_id, name=name, category=category, manufacturer=manufacturer, model=model,
                                        serial_number=serial, department=department, location=location, installation_date=today - timedelta(days=800),
                                        last_calibration_date=today - timedelta(days=320), next_calibration_due=today + timedelta(days=due_days),
                                        calibration_frequency_months=12, operational_status=status, assigned_technician=technician))
    db.session.add_all(equipment_rows)
    db.session.flush()
    for index, item in enumerate(equipment_rows[:4]):
        tech = item.assigned_technician
        db.session.add(CalibrationRecord(record_code=f"CAL-DEMO-{index + 1:03}", equipment=item, technician=tech,
                                         calibration_date=item.last_calibration_date, next_due_date=item.next_calibration_due,
                                         technician_name=tech.name, result="Passed", status="Passed", reference_standard="Demo Electrical Safety Analyzer",
                                         certificate_number=f"CERT-DEMO-{index + 1:03}", remarks="Demonstration calibration record."))
    db.session.commit()


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)