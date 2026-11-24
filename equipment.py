from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from auth import admin_required, log_action
from extensions import db
from models import Equipment, Technician
from qr_routes import ensure_qr

equipment_bp = Blueprint("equipment", __name__, url_prefix="/equipment")


def parse_date(value):
    return date.fromisoformat(value) if value else None


def equipment_form_values():
    fields = {key: request.form.get(key, "").strip() for key in (
        "equipment_id", "name", "category", "manufacturer", "model", "serial_number", "department", "location",
        "installation_date", "last_calibration_date", "next_calibration_due", "calibration_frequency_months",
        "operational_status", "assigned_technician_id", "notes")}
    required = ("equipment_id", "name", "category", "department")
    if any(not fields[key] for key in required):
        raise ValueError("Equipment ID, name, category, and department are required.")
    if fields["calibration_frequency_months"] and not fields["calibration_frequency_months"].isdigit():
        raise ValueError("Calibration frequency must be a whole number of months.")
    return fields


def apply_form(equipment, fields):
    equipment.equipment_id = fields["equipment_id"].upper()
    equipment.name = fields["name"]
    equipment.category = fields["category"]
    equipment.manufacturer = fields["manufacturer"]
    equipment.model = fields["model"]
    equipment.serial_number = fields["serial_number"] or None
    equipment.department = fields["department"]
    equipment.location = fields["location"]
    equipment.installation_date = parse_date(fields["installation_date"])
    equipment.last_calibration_date = parse_date(fields["last_calibration_date"])
    equipment.next_calibration_due = parse_date(fields["next_calibration_due"])
    equipment.calibration_frequency_months = int(fields["calibration_frequency_months"] or 12)
    equipment.operational_status = fields["operational_status"] or "Active"
    equipment.assigned_technician = db.session.get(Technician, int(fields["assigned_technician_id"])) if fields["assigned_technician_id"] else None
    equipment.notes = fields["notes"]


@equipment_bp.get("/")
@login_required
def listing():
    search = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    department = request.args.get("department", "").strip()
    query = Equipment.query
    if search:
        like = f"%{search}%"
        query = query.outerjoin(Technician).filter(or_(Equipment.equipment_id.ilike(like), Equipment.name.ilike(like), Equipment.serial_number.ilike(like), Equipment.department.ilike(like), Technician.name.ilike(like)))
    if department:
        query = query.filter(Equipment.department == department)
    rows = query.order_by(Equipment.name).all()
    if status:
        rows = [item for item in rows if item.calibration_status == status]
    return render_template("equipment.html", equipment=rows, search=search, selected_status=status,
                           selected_department=department, departments=sorted({item.department for item in Equipment.query.all()}))


@equipment_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        try:
            equipment = Equipment()
            apply_form(equipment, equipment_form_values())
            db.session.add(equipment)
            db.session.flush()
            ensure_qr(equipment)
            log_action("Equipment added", equipment.equipment_id)
            db.session.commit()
            flash("Equipment added and QR label generated.", "success")
            return redirect(url_for("equipment.details", equipment_id=equipment.id))
        except ValueError as error:
            db.session.rollback()
            flash(str(error), "danger")
        except Exception:
            db.session.rollback()
            flash("Could not save equipment. Check that the equipment ID and serial number are unique.", "danger")
    return render_template("equipment_form.html", equipment=None, technicians=Technician.query.order_by(Technician.name).all(), title="Add equipment")


@equipment_bp.get("/<int:equipment_id>")
@login_required
def details(equipment_id):
    equipment = db.get_or_404(Equipment, equipment_id)
    ensure_qr(equipment)
    return render_template("equipment_details.html", equipment=equipment)


@equipment_bp.route("/<int:equipment_id>/edit", methods=["GET", "POST"])
@login_required
def edit(equipment_id):
    equipment = db.get_or_404(Equipment, equipment_id)
    if request.method == "POST":
        try:
            apply_form(equipment, equipment_form_values())
            log_action("Equipment edited", equipment.equipment_id)
            db.session.commit()
            flash("Equipment details updated.", "success")
            return redirect(url_for("equipment.details", equipment_id=equipment.id))
        except ValueError as error:
            flash(str(error), "danger")
        except Exception:
            db.session.rollback()
            flash("Could not update equipment. Check that the ID and serial number are unique.", "danger")
    return render_template("equipment_form.html", equipment=equipment, technicians=Technician.query.order_by(Technician.name).all(), title="Edit equipment")


@equipment_bp.post("/<int:equipment_id>/delete")
@login_required
@admin_required
def delete(equipment_id):
    equipment = db.get_or_404(Equipment, equipment_id)
    identifier = equipment.equipment_id
    log_action("Equipment deleted", identifier)
    db.session.delete(equipment)
    db.session.commit()
    flash("Equipment and its calibration history were deleted.", "success")
    return redirect(url_for("equipment.listing"))