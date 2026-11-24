import secrets
from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from auth import log_action
from extensions import db
from models import CalibrationRecord, Equipment, Technician

calibration_bp = Blueprint("calibration", __name__, url_prefix="/calibration")
RESULTS = ("Passed", "Failed", "Adjustment Required")


@calibration_bp.route("/new", methods=["GET", "POST"])
@login_required
def create():
    equipment_rows = Equipment.query.order_by(Equipment.name).all()
    technicians = Technician.query.order_by(Technician.name).all()
    selected_id = request.args.get("equipment", type=int)
    if request.method == "POST":
        try:
            equipment = db.get_or_404(Equipment, request.form.get("equipment_id", type=int))
            calibration_date = date.fromisoformat(request.form.get("calibration_date", ""))
            next_due = date.fromisoformat(request.form.get("next_due_date", ""))
            result = request.form.get("result", "")
            if result not in RESULTS or next_due <= calibration_date:
                raise ValueError
            technician = db.session.get(Technician, request.form.get("technician_id", type=int)) if request.form.get("technician_id") else None
            technician_name = technician.name if technician else request.form.get("technician_name", "").strip()
            if not technician_name:
                raise ValueError
            record = CalibrationRecord(record_code=f"CAL-{secrets.token_hex(4).upper()}", equipment=equipment,
                                       technician=technician, calibration_date=calibration_date, next_due_date=next_due,
                                       technician_name=technician_name, result=result, status="Passed" if result == "Passed" else "Failed",
                                       reference_standard=request.form.get("reference_standard", "").strip(),
                                       certificate_number=request.form.get("certificate_number", "").strip(),
                                       remarks=request.form.get("remarks", "").strip())
            db.session.add(record)
            equipment.last_calibration_date = calibration_date
            equipment.next_calibration_due = next_due
            log_action(f"Calibration record added ({result})", equipment.equipment_id)
            db.session.commit()
            flash("Calibration saved. Equipment due date updated; previous history retained.", "success")
            return redirect(url_for("calibration.history", equipment_id=equipment.id))
        except (ValueError, TypeError):
            db.session.rollback()
            flash("Enter valid dates, a technician name, and a valid calibration result. Next due date must be after calibration date.", "danger")
    return render_template("calibration_form.html", equipment=equipment_rows, technicians=technicians, selected_id=selected_id, results=RESULTS, today=date.today().isoformat())


@calibration_bp.get("/history")
@login_required
def history():
    equipment_id = request.args.get("equipment_id", type=int)
    query = CalibrationRecord.query.join(Equipment)
    if equipment_id:
        query = query.filter(CalibrationRecord.equipment_id == equipment_id)
    records = query.order_by(CalibrationRecord.calibration_date.desc()).all()
    return render_template("calibration_history.html", records=records, equipment=Equipment.query.order_by(Equipment.name).all(), selected_id=equipment_id)