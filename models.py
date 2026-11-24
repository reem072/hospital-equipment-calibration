import secrets
from datetime import date

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False, default="Technician")
    active = db.Column(db.Boolean, nullable=False, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Technician(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    employee_id = db.Column(db.String(40), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(40), default="")
    role = db.Column(db.String(60), default="Biomedical Engineer/Technician")

    equipment = db.relationship("Equipment", back_populates="assigned_technician")
    calibrations = db.relationship("CalibrationRecord", back_populates="technician")


class Equipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.String(40), unique=True, nullable=False)
    qr_token = db.Column(db.String(64), unique=True, nullable=False, default=lambda: secrets.token_urlsafe(24))
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    manufacturer = db.Column(db.String(120), default="")
    model = db.Column(db.String(120), default="")
    serial_number = db.Column(db.String(120), unique=True, nullable=True)
    department = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(120), default="")
    installation_date = db.Column(db.Date, nullable=True)
    last_calibration_date = db.Column(db.Date, nullable=True)
    next_calibration_due = db.Column(db.Date, nullable=True)
    calibration_frequency_months = db.Column(db.Integer, nullable=False, default=12)
    operational_status = db.Column(db.String(30), nullable=False, default="Active")
    assigned_technician_id = db.Column(db.Integer, db.ForeignKey("technician.id"), nullable=True)
    notes = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())

    assigned_technician = db.relationship("Technician", back_populates="equipment")
    calibrations = db.relationship("CalibrationRecord", back_populates="equipment", cascade="all, delete-orphan", order_by="CalibrationRecord.calibration_date.desc()")

    @property
    def calibration_status(self):
        if self.operational_status == "Under Maintenance":
            return "UNDER MAINTENANCE"
        if self.calibrations and self.calibrations[0].result != "Passed":
            return "FAILED" if self.calibrations[0].result == "Failed" else "ADJUSTMENT REQUIRED"
        if not self.next_calibration_due:
            return "NOT SCHEDULED"
        days = (self.next_calibration_due - date.today()).days
        if days < 0:
            return "OVERDUE"
        if days <= 30:
            return "DUE SOON"
        return "VALID"


class CalibrationRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    record_code = db.Column(db.String(40), unique=True, nullable=False)
    equipment_id = db.Column(db.Integer, db.ForeignKey("equipment.id"), nullable=False)
    technician_id = db.Column(db.Integer, db.ForeignKey("technician.id"), nullable=True)
    calibration_date = db.Column(db.Date, nullable=False)
    next_due_date = db.Column(db.Date, nullable=False)
    technician_name = db.Column(db.String(120), nullable=False)
    result = db.Column(db.String(40), nullable=False)
    status = db.Column(db.String(30), nullable=False)
    reference_standard = db.Column(db.String(160), default="")
    certificate_number = db.Column(db.String(80), default="")
    remarks = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())

    equipment = db.relationship("Equipment", back_populates="calibrations")
    technician = db.relationship("Technician", back_populates="calibrations")


class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    username = db.Column(db.String(80), nullable=False)
    action = db.Column(db.String(160), nullable=False)
    equipment_identifier = db.Column(db.String(40), default="")

    user = db.relationship("User")