from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv
import random
import base64
from openpyxl import Workbook, load_workbook
from threading import Lock
from datetime import datetime
import smtplib
import socket
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.getenv("SECRET_KEY", "secret123")

UPLOAD_FOLDER = "/tmp/audio_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

EXCEL_FILE = "/tmp/complaints.xlsx"
excel_lock = Lock()

# ================== EXCEL ==================
def create_excel():
    if not os.path.exists(EXCEL_FILE):
        wb = Workbook()
        ws = wb.active
        ws.append([
            "ID","Complaint ID","Name","Address","Contact","Email",
            "Unit","WO","Quarter","Complaint","Category",
            "Subcategory","Reply","Audio","Date"
        ])
        wb.save(EXCEL_FILE)

create_excel()

def save_to_excel(data):
    with excel_lock:
        wb = load_workbook(EXCEL_FILE)
        ws = wb.active
        next_id = ws.max_row
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        ws.append([
            next_id,
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

# ================== EMAIL ==================
def send_email(subject, body, attachment_path=None):
    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASS = os.getenv("SMTP_PASS")

    if not SMTP_SERVER or not SMTP_USER or not SMTP_PASS:
        return

    try:
        socket.gethostbyname(SMTP_SERVER)

        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = SMTP_USER
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition',
                                f'attachment; filename={os.path.basename(attachment_path)}')
                msg.attach(part)

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
        server.quit()

    except Exception as e:
        print("Email Error:", e)

# ================== ROUTES ==================
@app.route('/')
def landing():
    return render_template("landing.html")

@app.route('/complaint', methods=['GET', 'POST'])
def complaint():
    if request.method == 'POST':
        try:
            complaint_id = "CMP" + str(random.randint(10000, 99999))

            data = {
                "complaint_id": complaint_id,
                "name": request.form.get('name'),
                "address": request.form.get('address'),
                "contact": request.form.get('contact'),
                "email": request.form.get('email'),
                "unit": request.form.get('unit'),
                "wo": request.form.get('wo'),
                "quarter": request.form.get('quarter'),
                "complaint": request.form.get('complaint'),
                "category": request.form.get('category'),
                "subcategory": request.form.get('subcategory'),
                "reply": "Pending",
                "audio": ""
            }

            audio_data = request.form.get("audio_data")
            audio_path = None

            if audio_data:
                header, encoded = audio_data.split(",", 1)
                file_data = base64.b64decode(encoded)
                filepath = os.path.join(UPLOAD_FOLDER, f"{complaint_id}.webm")

                with open(filepath, "wb") as f:
                    f.write(file_data)

                data["audio"] = filepath
                audio_path = filepath

            save_to_excel(data)

            email_body = f"""
Complaint ID: {data['complaint_id']}
Name: {data['name']}
Contact: {data['contact']}
Complaint: {data['complaint']}
"""

            send_email("New Complaint Submitted", email_body, audio_path)

            return jsonify({"status": "success", "id": complaint_id})

        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})

    # ✅ ONLY THIS LINE (IMPORTANT)
    return render_template("complaint.html")

# ================== RUN ==================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)