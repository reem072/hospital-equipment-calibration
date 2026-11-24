# Smart Hospital Biomedical Equipment Calibration Reminder and Tracking System

A beginner-friendly Flask and SQLite academic prototype for biomedical equipment inventory, QR identification, calibration tracking, reminders, and printable reports. It does not store patient information.

## Project files

| File/folder | Purpose |
| --- | --- |
| `app.py` | Flask application factory, dashboard, reports, activity log, and sample-data setup |
| `models.py` | SQLAlchemy models and relationships for users, equipment, technicians, calibrations, and activity |
| `extensions.py` | Shared database, login, and CSRF extensions |
| `auth.py` | Login, logout, role helper, and activity recording |
| `equipment.py` | Equipment search, filters, create, read, update, and admin-only delete |
| `calibration.py` | Calibration form and append-only calibration history |
| `qr_routes.py` | Private-token QR generation, scanning, lookup, and print labels |
| `templates/` | Jinja HTML pages, including the shared Bootstrap layout |
| `static/css/style.css` | Responsive visual design and print rules |
| `static/js/app.js` | Mobile sidebar behavior |
| `static/js/charts.js` | Dashboard Chart.js visualizations |
| `static/js/scanner.js` | Browser camera QR scanner using html5-qrcode |
| `static/qrcodes/` | Generated QR label images (created automatically) |
| `database/calibration.db` | Local SQLite database (created and seeded automatically) |
| `tests/test_workflows.py` | Isolated smoke/integration tests |

## Windows setup (VS Code)

Use Python 3.10 or later. Open this folder in VS Code, then open **Terminal > New Terminal**. The commands below use the Windows Python launcher (`py`); if your installation uses `python`, replace `py -3` with `python`.

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
```

If PowerShell prevents environment activation, either run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal and activate again, or use Command Prompt and run `.venv\Scripts\activate.bat`.

## Database setup

No manual SQL command is necessary. On the first app start, SQLAlchemy creates `database/calibration.db` and seeds two demonstration logins, two technicians, five equipment records, and four calibration records. The seed includes valid, due-soon, overdue, and under-maintenance equipment. Restarting the app will not duplicate the sample data.

To rebuild the demonstration database, stop Flask and delete `database/calibration.db`; the next app start creates and seeds it again. This removes changes made in the demo.

## Run the application

```powershell
py app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). For another device on the same local network, run `py -c "import socket; print(socket.gethostbyname(socket.gethostname()))"` and open `http://YOUR-COMPUTER-IP:5000` on that device. Allow the Windows firewall prompt only for a trusted private network. Camera scanning works on localhost or HTTPS; browsers normally block camera access on ordinary HTTP LAN addresses.

## Demonstration logins

- Admin: username `admin`, password `Admin123!`
- Technician: username `technician`, password `Tech123!`

These are public demo credentials, not secure production accounts. For a longer demonstration, configure an environment `SECRET_KEY` before starting Flask. Example PowerShell: `$env:SECRET_KEY = "your-long-random-demo-secret"`. The app uses a random key if this variable is omitted; sessions will then be invalidated when the app restarts.

## Recommended demonstration workflow

1. Sign in as `admin` and review the dashboard cards, charts, due-soon list, reminders, and recent calibration activity.
2. Open **Equipment > Add equipment**. Enter a unique equipment ID and serial number, choose the department/category, and set a next calibration date. Save to generate its QR token and label.
3. Open the equipment record. The summary, calibration status, due dates, assigned technician, QR image, and retained calibration history appear here. Use **Print QR label** to print the label.
4. Open **QR Scanner > Start camera** and allow camera permission. Point the camera at a printed label or an on-screen label. The QR carries a random record token; the destination still requires login. If camera access is unavailable, paste the QR's URL/token into the manual lookup box.
5. From the equipment record choose **Record calibration**. Enter the calibration date, next due date, technician, result, and any certificate/reference details. A new history record is appended and the equipment's current calibration dates update.
6. Review **Calibration History**, the dashboard reminders, and **Reports**. The report tabs can be printed using the browser print dialog.

## Tests

```powershell
py -m unittest discover -s tests -v
```

## Troubleshooting

- **`python` opens the Microsoft Store:** use `py -3 app.py` or `py -3 -m pip install -r requirements.txt`. Confirm the launcher with `py --version`.
- **`ModuleNotFoundError`:** activate `.venv` and run `py -m pip install -r requirements.txt` again. In VS Code, choose the `.venv` interpreter with **Python: Select Interpreter**.
- **PowerShell says script execution is disabled:** use the process-only execution policy command above, or activate the environment from Command Prompt.
- **Login returns to the login page:** use the seeded credentials exactly as listed. The default database is in `database/calibration.db`, not the original `equipment.db`.
- **Camera does not start:** grant camera permission in the browser, close other camera apps/tabs, use localhost or HTTPS, and use the manual QR value field as a fallback.
- **QR points to a different computer:** the QR URL is generated using the app's local host/port. Run the server from the computer that will host the demo, then create/refresh labels from that host. For multi-device LAN use, configure a reachable HTTPS host and camera permission policy.
- **Port 5000 is already in use:** stop the other Flask process, or change `app.run(debug=True)` in `app.py` to `app.run(debug=True, port=5001)` and use `http://127.0.0.1:5001`.
- **Cannot save equipment:** equipment ID and serial number must be unique. Required values are equipment ID, name, category, and department.

## Prototype security scope

The system hashes passwords, protects routes behind login, uses role checks for technician administration and equipment deletion, enables Flask-WTF CSRF protection, uses SQLAlchemy query parameters, sets HTTP-only and same-site session cookies, and prints random QR tokens rather than equipment details. Production deployment needs HTTPS, managed secrets, backups, audit/retention policies, stronger account administration, and institutional validation. Do not enter patient data.