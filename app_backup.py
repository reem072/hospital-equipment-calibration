from flask import Flask, render_template, request

app = Flask(__name__)

equipment = {
    "ECG-001": {
        "name": "ECG Machine",
        "department": "ICU",
        "manufacturer": "To be entered",
        "model": "To be entered",
        "serial": "To be entered",
        "last_calibration": "15-Mar-2026",
        "next_calibration": "15-Sep-2026"
    },

    "BP-014": {
        "name": "Blood Pressure Monitor",
        "department": "Ward",
        "manufacturer": "To be entered",
        "model": "To be entered",
        "serial": "To be entered",
        "last_calibration": "01-Apr-2026",
        "next_calibration": "01-Oct-2026"
    },

    "WS-005": {
        "name": "Patient Weighing Scale",
        "department": "OPD",
        "manufacturer": "To be entered",
        "model": "To be entered",
        "serial": "To be entered",
        "last_calibration": "10-May-2026",
        "next_calibration": "10-Nov-2026"
    },

    "PO-007": {
        "name": "Pulse Oximeter",
        "department": "Ward",
        "manufacturer": "To be entered",
        "model": "To be entered",
        "serial": "To be entered",
        "last_calibration": "20-Mar-2026",
        "next_calibration": "20-Sep-2026"
    },

    "PM-023": {
        "name": "Patient Monitor",
        "department": "ICU",
        "manufacturer": "To be entered",
        "model": "To be entered",
        "serial": "To be entered",
        "last_calibration": "05-Apr-2026",
        "next_calibration": "05-Oct-2026"
    }
}


@app.route("/", methods=["GET", "POST"])
def index():

    result = None
    scanned_id = ""

    if request.method == "POST":

        scanned_id = request.form.get(
            "equipment_id", ""
        ).strip().upper()

        if scanned_id in equipment:

            result = equipment[scanned_id]
            result["id"] = scanned_id

        else:

            result = "Equipment not found"

    return render_template(
        "index.html",
        result=result,
        scanned_id=scanned_id
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)