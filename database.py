import sqlite3

conn = sqlite3.connect("equipment.db")

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS equipment (
    equipment_id TEXT PRIMARY KEY,
    equipment_name TEXT NOT NULL,
    department TEXT,
    manufacturer TEXT,
    model TEXT,
    serial_number TEXT,
    last_calibration TEXT,
    next_calibration TEXT
)
""")

equipment_data = [
    (
        "ECG-001",
        "ECG Machine",
        "ICU",
        "Philips",
        "PageWriter TC20",
        "ECG2026001",
        "2026-03-15",
        "2026-09-15"
    ),
    (
        "BP-001",
        "Digital BP Monitor",
        "General Ward",
        "Omron",
        "HEM-7120",
        "BP2026001",
        "2026-04-10",
        "2027-04-10"
    ),
    (
        "SPO2-001",
        "Pulse Oximeter",
        "ICU",
        "Masimo",
        "Rad-5",
        "SPO22026001",
        "2026-02-20",
        "2027-02-20"
    ),
    (
        "VENT-001",
        "Ventilator",
        "ICU",
        "Drager",
        "Evita V500",
        "VENT2026001",
        "2026-01-15",
        "2027-01-15"
    ),
    (
        "DEF-001",
        "Defibrillator",
        "Emergency",
        "Philips",
        "HeartStart XL",
        "DEF2026001",
        "2026-05-05",
        "2027-05-05"
    )
]

cursor.executemany("""
INSERT OR REPLACE INTO equipment
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", equipment_data)

conn.commit()
conn.close()

print("Equipment database created successfully!")
print("5 equipment records added.")