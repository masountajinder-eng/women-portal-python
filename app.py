from flask import Flask, render_template, request, jsonify, send_file, redirect, session
import os
from dotenv import load_dotenv
import random
import base64
from openpyxl import Workbook, load_workbook
from threading import Lock
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# ================= INIT =================
load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.getenv("SECRET_KEY", "secret123")

print("🔥 FINAL SYSTEM WITH ADMIN LOGIN RUNNING")

# ================= ADMIN LOGIN =================
ADMIN_USER = "237engrregt"
ADMIN_PASS = "237237chakde"

# ================= EMAIL CONFIG =================
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

def send_alert_email(data):
    try:
        msg = MIMEMultipart()
        msg['Subject'] = "🚨 237 Engr Regt - New Complaint Alert"
        msg['From'] = SMTP_USER
        msg['To'] = SMTP_USER

        body = f"""
🚨 237 Engr Regt 🚨

Complaint ID: {data['complaint_id']}
Name: {data['name']}
Contact: {data['contact']}
Category: {data['category']}
Subcategory: {data['subcategory']}

Complaint:
{data['complaint']}
"""
        msg.attach(MIMEText(body, 'plain'))

        # AUDIO
        if data.get("audio") and os.path.exists(data["audio"]):
            with open(data["audio"], "rb") as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename=audio.webm')
                msg.attach(part)

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()

        print("✅ EMAIL SENT")

    except Exception as e:
        print("❌ EMAIL ERROR:", e)

# ================= PATH =================
UPLOAD_FOLDER = "/tmp/audio_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

EXCEL_FILE = "/tmp/complaints.xlsx"

# ================= EXCEL =================
excel_lock = Lock()

def create_excel():
    if not os.path.exists(EXCEL_FILE):
        wb = Workbook()
        ws = wb.active
        ws.append([
            "ID","Complaint ID","Name","Address","Contact",
            "Email","Unit","WO","Quarter","Complaint",
            "Category","Subcategory","Reply","Audio","Date"
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
            data["complaint_id"],
            data["name"],
            data["address"],
            data["contact"],
            data["email"],
            data["unit"],
            data["wo"],
            data["quarter"],
            data["complaint"],
            data["category"],
            data["subcategory"],
            data["reply"],
            data["audio"],
            now
        ])
        wb.save(EXCEL_FILE)

# ================= ROUTES =================

@app.route('/')
def home():
    return render_template("landing.html")

# 🔐 LOGIN PAGE
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        user = request.form.get("username")
        pwd = request.form.get("password")

        if user == ADMIN_USER and pwd == ADMIN_PASS:
            session['admin'] = True
            return redirect("/admin")
        else:
            return "❌ Wrong credentials"

    return render_template("login.html")

# 🔓 LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    return redirect("/login")

# 📝 COMPLAINT
@app.route('/complaint', methods=['GET','POST'])
def complaint():

    if request.method == 'POST':
        complaint_id = "CMP" + str(random.randint(10000,99999))

        data = {
            "complaint_id": complaint_id,
            "name": request.form.get('name',''),
            "address": request.form.get('address',''),
            "contact": request.form.get('contact',''),
            "email": request.form.get('email',''),
            "unit": request.form.get('unit',''),
            "wo": request.form.get('wo',''),
            "quarter": request.form.get('quarter',''),
            "complaint": request.form.get('complaint',''),
            "category": request.form.get('category',''),
            "subcategory": request.form.get('subcategory',''),
            "reply": "Pending",
            "audio": ""
        }

        # AUDIO
        audio_data = request.form.get("audio_data")
        if audio_data and "," in audio_data:
            header, encoded = audio_data.split(",",1)
            filepath = os.path.join(UPLOAD_FOLDER, f"{complaint_id}.webm")
            with open(filepath,"wb") as f:
                f.write(base64.b64decode(encoded))
            data["audio"] = filepath

        save_to_excel(data)
        send_alert_email(data)

        return jsonify({"status":"success","id":complaint_id})

    return render_template("complaint.html")

# 📊 ADMIN PANEL
@app.route('/admin')
def admin():
    if not session.get('admin'):
        return redirect("/login")

    wb = load_workbook(EXCEL_FILE)
    ws = wb.active

    data = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        data.append({
            "complaint_id": row[1],
            "name": row[2],
            "complaint": row[9],
            "category": row[10],
            "subcategory": row[11],
            "reply": row[12],
            "audio": row[13]
        })

    return render_template("admin.html", data=data)

# 🔍 TRACK
@app.route('/track', methods=['GET','POST'])
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

# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)