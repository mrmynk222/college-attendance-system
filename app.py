from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)



from flask import Flask, render_template, request, redirect, send_from_directory
import qrcode
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

DB_PATH = "database.db"
QR_DIR = "qr_codes"

# ---------- DATABASE SETUP ----------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            roll TEXT UNIQUE,
            qr_path TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll TEXT,
            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ensure qr directory exists
if not os.path.exists(QR_DIR):
    os.makedirs(QR_DIR)

# ---------- HOME ----------
@app.route('/')
def home():
    return render_template("index.html")

# ---------- GENERATE QR ----------
@app.route('/generate', methods=['GET', 'POST'])
def generate():
    if request.method == 'POST':
        name = request.form['name'].strip()
        roll = request.form['roll'].strip()

        if not name or not roll:
            return "Name and Roll required", 400

        # generate QR image (data is roll number)
        data = f"{roll}"
        img = qrcode.make(data)
        qr_path = os.path.join(QR_DIR, f"{roll}.png")
        img.save(qr_path)

        # save student if not exists
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("INSERT OR REPLACE INTO students(name, roll, qr_path) VALUES(?,?,?)",
                    (name, roll, qr_path))
        conn.commit()
        conn.close()

        return redirect('/')
    return render_template("generate_qr.html")

# Serve QR images
@app.route('/qr_codes/<path:filename>')
def qr_file(filename):
    return send_from_directory(QR_DIR, filename)

# ---------- SCAN QR (Attendance Marking) ----------
@app.route('/scan', methods=['GET', 'POST'])
def scan():
    if request.method == 'POST':
        roll = request.form.get('qr_value', '').strip()
        if not roll:
            return "No QR value received", 400

        # record attendance
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("INSERT INTO attendance(roll) VALUES(?)", (roll,))
        conn.commit()
        conn.close()

        return "Attendance Marked Successfully for roll: " + roll
    return render_template("scan.html")

# ---------- VIEW ATTENDANCE ----------
@app.route('/attendance')
def view_attendance():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, roll, time FROM attendance ORDER BY time DESC")
    data = cur.fetchall()
    conn.close()
    return render_template("attendance.html", data=data)

# ---------- SIMPLE STUDENT LIST (optional) ----------
@app.route('/students')
def view_students():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, name, roll, qr_path FROM students")
    s = cur.fetchall()
    conn.close()
    return render_template("students.html", students=s)

# ---------- RUN ----------
if __name__ == '__main__':
    # run on localhost:5000
    app.run(debug=True)

