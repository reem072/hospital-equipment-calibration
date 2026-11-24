from pathlib import Path

import qrcode
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import login_required

from extensions import db
from models import Equipment

qr_bp = Blueprint("qr", __name__)
QR_DIR = Path(__file__).resolve().parent / "static" / "qrcodes"


def ensure_qr(equipment):
    QR_DIR.mkdir(parents=True, exist_ok=True)
    path = QR_DIR / f"{equipment.qr_token}.png"
    if not path.exists():
        qrcode.make(url_for("qr.scan_token", token=equipment.qr_token, _external=True)).save(path)


@qr_bp.get("/scanner")
@login_required
def scanner():
    return render_template("scanner.html")


@qr_bp.get("/scan/<token>")
@login_required
def scan_token(token):
    equipment = Equipment.query.filter_by(qr_token=token).first()
    if not equipment:
        flash("Equipment record not found.", "danger")
        return redirect(url_for("qr.scanner"))
    return redirect(url_for("equipment.details", equipment_id=equipment.id))


@qr_bp.post("/scan/lookup")
@login_required
def scan_lookup():
    token = request.form.get("token", "").strip()
    equipment = Equipment.query.filter_by(qr_token=token).first() if token else None
    if not equipment:
        flash("Equipment record not found.", "danger")
        return redirect(url_for("qr.scanner"))
    return redirect(url_for("equipment.details", equipment_id=equipment.id))


@qr_bp.get("/equipment/<int:equipment_id>/label")
@login_required
def label(equipment_id):
    equipment = db.get_or_404(Equipment, equipment_id)
    ensure_qr(equipment)
    return render_template("qr_label.html", equipment=equipment)