from flask import Flask, render_template, request, jsonify, send_file, redirect, session
import sqlite3
import os
from dotenv import load_dotenv
import resend
import random
import base64
from openpyxl import Workbook

load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = "secret123"

resend.api_key = os.environ.get("RESEND_API_KEY")

print("🔥 FINAL ULTRA PRO CODE RUNNING")

# 🔐 ADMIN LOGIN
ADMIN_USER = "admin"
ADMIN_PASS = "1234"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static/audio")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# -------- DATABASE --------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id TEXT,
            name TEXT,
            address TEXT,
            contact TEXT,
            email TEXT,
            unit TEXT,
            wo TEXT,
            quarter TEXT,
            complaint TEXT,
            category TEXT,
            subcategory TEXT,
            reply TEXT,
            audio TEXT
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# -------- EMAIL --------
def send_email(data, audio_link=None):
    try:
        audio_html = ""

        if audio_link:
            full_url = f"https://women-portal.onrender.com{audio_link}"

            audio_html = f'''
            <p><b>🎧 Audio:</b>
            <a href="{full_url}">Listen</a></p>
            '''

        resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": ["masountajinder@gmail.com"],
            "subject": f"🚨 Complaint {data[0]}",
            "html": f"""
                <h2>New Complaint</h2>
                <p><b>ID:</b> {data[0]}</p>
                <p><b>Name:</b> {data[1]}</p>
                <p><b>Contact:</b> {data[3]}</p>
                <p><b>Category:</b> {data[8]}</p>
                <p><b>Complaint:</b><br>{data[10]}</p>
                {audio_html}
            """
        })

        print("✅ Email Sent")

    except Exception as e:
        print("❌ Email error:", str(e))


# -------- ROUTES --------

@app.route('/')
def landing():
    return render_template("landing.html")


@app.route('/complaint', methods=['GET', 'POST'])
def complaint():
    if request.method == 'POST':
        try:
            complaint_id = "CMP" + str(random.randint(10000, 99999))

            name = request.form.get('name')
            address = request.form.get('address')
            contact = request.form.get('contact')
            email = request.form.get('email')
            unit = request.form.get('unit')
            wo = request.form.get('wo')
            quarter = request.form.get('quarter')
            category = request.form.get('category')
            subcategory = request.form.get('subcategory')
            complaint_text = request.form.get('complaint')

            audio_data = request.form.get("audio")
            audio_path = ""

            if audio_data:
                header, encoded = audio_data.split(",", 1)
                file_data = base64.b64decode(encoded)

                filename = f"{complaint_id}.webm"
                filepath = os.path.join(UPLOAD_FOLDER, filename)

                with open(filepath, "wb") as f:
                    f.write(file_data)

                audio_path = f"/static/audio/{filename}"

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()

            c.execute("""
                INSERT INTO complaints 
                (complaint_id, name, address, contact, email, unit, wo, quarter, complaint, category, subcategory, reply, audio)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                complaint_id, name, address, contact, email,
                unit, wo, quarter, complaint_text,
                category, subcategory, "", audio_path
            ))

            conn.commit()
            conn.close()

            send_email((
                complaint_id, name, address, contact, email,
                unit, wo, quarter, category, subcategory, complaint_text
            ), audio_path)

            return jsonify({"status": "success", "id": complaint_id})

        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})

    return render_template("complaint.html")


# -------- ADMIN LOGIN --------
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == "POST":
        user = request.form.get("username")
        password = request.form.get("password")

        if user == ADMIN_USER and password == ADMIN_PASS:
            session['admin'] = True
            return redirect("/dashboard")
        else:
            return "❌ Wrong Credentials"

    return render_template("admin_login.html")


# -------- DASHBOARD --------
@app.route('/dashboard')
def dashboard():
    if not session.get('admin'):
        return redirect("/admin")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM complaints")
    data = cursor.fetchall()
    conn.close()

    return render_template("admin.html", data=data)


# -------- REPLY SYSTEM --------
@app.route("/reply/<cid>", methods=["POST"])
def reply(cid):
    if not session.get('admin'):
        return jsonify({"status": "error"})

    reply_text = request.form.get("reply")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("UPDATE complaints SET reply=? WHERE complaint_id=?", (reply_text, cid))
    conn.commit()
    conn.close()

    return jsonify({"status": "success"})


# -------- DELETE SYSTEM --------
@app.route("/delete/<cid>", methods=["POST"])
def delete(cid):
    if not session.get('admin'):
        return jsonify({"status": "error"})

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM complaints WHERE complaint_id=?", (cid,))
    conn.commit()
    conn.close()

    return jsonify({"status": "success"})


# -------- LIVE CHECK --------
@app.route("/check")
def check():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM complaints")
    count = cursor.fetchone()[0]

    conn.close()

    return jsonify({"count": count})


# -------- LOGOUT --------
@app.route('/logout')
def logout():
    session.clear()
    return redirect("/admin")


# -------- DOWNLOAD EXCEL --------
@app.route("/download-excel")
def download_excel():
    if not session.get('admin'):
        return redirect("/admin")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT complaint_id, name, address, contact, email,
               unit, wo, quarter, category, subcategory,
               complaint, audio
        FROM complaints
    """)

    data = cursor.fetchall()
    conn.close()

    wb = Workbook()
    ws = wb.active
    ws.title = "Complaints"

    ws.append([
        "Complaint ID", "Name", "Address", "Contact", "Email",
        "Unit", "WO", "Quarter", "Category", "Subcategory",
        "Complaint", "Audio"
    ])

    for row in data:
        ws.append(row)

    file_path = os.path.join(BASE_DIR, "complaints.xlsx")
    wb.save(file_path)

    return send_file(file_path, as_attachment=True)


# -------- RUN --------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)