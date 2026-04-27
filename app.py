from flask import Flask, render_template, request, jsonify, send_file, redirect
import os
from dotenv import load_dotenv
import random
import base64
from openpyxl import Workbook, load_workbook
from threading import Lock
from datetime import datetime
import smtplib
from email.mime.text import MIMEText

# ================= INIT =================
load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.getenv("SECRET_KEY", "secret123")

print("🔥 FINAL SYSTEM WITH EMAIL ALERT RUNNING")

# ================= EMAIL CONFIG =================
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

def send_alert_email(data):
    try:
        msg = MIMEText(f"""
🚨 NEW COMPLAINT RECEIVED 🚨

Complaint ID: {data['complaint_id']}
Name: {data['name']}
Contact: {data['contact']}
Category: {data['category']}
Subcategory: {data['subcategory']}

Complaint:
{data['complaint']}
        """)

        msg['Subject'] = "🚨 URGENT: New Complaint Submitted"
        msg['From'] = SMTP_USER
        msg['To'] = SMTP_USER

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()

        print("✅ Email Alert Sent")

    except Exception as e:
        print("❌ Email Error:", e)

# ================= PATH =================
UPLOAD_FOLDER = "audio_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

EXCEL_FILE = "complaints.xlsx"

# ================= EXCEL =================
excel_lock = Lock()

def create_excel():
    if not os.path.exists(EXCEL_FILE):
        wb = Workbook()
        ws = wb.active
        ws.append([
            "ID", "Complaint ID", "Name", "Address", "Contact",
            "Email", "Unit", "WO", "Quarter", "Complaint",
            "Category", "Subcategory", "Reply", "Audio", "Date"
        ])
        wb.save(EXCEL_FILE)

create_excel()

def save_to_excel(data):
    with excel_lock:
        wb = load_workbook(EXCEL_FILE)
        ws = wb.active
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        ws.append([
            ws.max_row,
            data.get("complaint_id"),
            data.get("name"),
            data.get("address"),
            data.get("contact"),
            data.get("email"),
            data.get("unit"),
            data.get("wo"),
            data.get("quarter"),
            data.get("complaint"),
            data.get("category"),
            data.get("subcategory"),
            data.get("reply"),
            data.get("audio"),
            now
        ])
        wb.save(EXCEL_FILE)

# ================= ROUTES =================

@app.route('/')
def home():
    return render_template("landing.html")

# ✅ COMPLAINT
@app.route('/complaint', methods=['GET', 'POST'])
def complaint():

    if request.method == 'POST':
        try:
            complaint_id = "CMP" + str(random.randint(10000, 99999))

            data = {
                "complaint_id": complaint_id,
                "name": request.form.get('name', ''),
                "address": request.form.get('address', ''),
                "contact": request.form.get('contact', ''),
                "email": request.form.get('email', ''),
                "unit": request.form.get('unit', ''),
                "wo": request.form.get('wo', ''),
                "quarter": request.form.get('quarter', ''),
                "complaint": request.form.get('complaint', ''),
                "category": request.form.get('category', ''),
                "subcategory": request.form.get('subcategory', ''),
                "reply": "Pending",
                "audio": ""
            }

            # 🎤 AUDIO SAVE
            audio_data = request.form.get("audio_data")
            if audio_data and "," in audio_data:
                try:
                    header, encoded = audio_data.split(",", 1)
                    file_data = base64.b64decode(encoded)
                    filepath = os.path.join(UPLOAD_FOLDER, f"{complaint_id}.webm")

                    with open(filepath, "wb") as f:
                        f.write(file_data)

                    data["audio"] = filepath
                except Exception as e:
                    print("⚠️ Audio error:", e)

            # ✅ SAVE
            save_to_excel(data)

            # 🔥 EMAIL ALERT
            send_alert_email(data)

            return jsonify({"status": "success", "id": complaint_id})

        except Exception as e:
            print("❌ ERROR:", e)
            return jsonify({"status": "error", "message": str(e)})

    return render_template("complaint.html")


# ✅ TRACK
@app.route('/track', methods=['GET', 'POST'])
def track():
    data = None

    if request.method == 'POST':
        cid = request.form.get("complaint_id")

        wb = load_workbook(EXCEL_FILE)
        ws = wb.active

        for row in ws.iter_rows(min_row=2, values_only=True):
            if str(row[1]) == cid:
                data = row
                break

    return render_template("track.html", data=data)


# ✅ ADMIN
@app.route('/admin')
def admin():
    wb = load_workbook(EXCEL_FILE)
    ws = wb.active
    data = list(ws.values)
    return render_template("admin.html", data=data)


# ✅ DOWNLOAD
@app.route("/download_excel")
def download_excel():
    return send_file(EXCEL_FILE, as_attachment=True)


# ✅ REPLY
@app.route('/reply/<cid>', methods=['POST'])
def reply(cid):
    reply_text = request.form.get("reply", "")

    wb = load_workbook(EXCEL_FILE)
    ws = wb.active

    for row in ws.iter_rows(min_row=2):
        if str(row[1].value) == cid:
            row[12].value = reply_text
            break

    wb.save(EXCEL_FILE)

    return redirect("/admin")


# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)