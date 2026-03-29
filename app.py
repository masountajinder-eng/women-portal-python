from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
import os
from dotenv import load_dotenv
import resend
import random

load_dotenv()

app = Flask(__name__)
app.secret_key = "secret123"

# API KEY
resend.api_key = os.environ.get("RESEND_API_KEY")

print("🔥 FINAL CODE RUNNING")
print("API KEY:", resend.api_key)

# -------- DATABASE --------
def init_db():
    conn = sqlite3.connect("database.db")
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
            reply TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# -------- EMAIL --------
def send_email(data):
    try:
        resend.Emails.send({
            "from": "onboarding@resend.dev",   # ✅ FIXED
            "to": ["masountajinder@gmail.com"],
            "subject": f"🚨 New Complaint {data[0]}",
            "html": f"""
                <h2>New Complaint Submitted</h2>
                <p><b>ID:</b> {data[0]}</p>
                <p><b>Name:</b> {data[1]}</p>
                <p><b>Email:</b> {data[4]}</p>
                <p><b>Contact:</b> {data[3]}</p>
                <p><b>Complaint:</b><br>{data[8] or "No complaint provided"}</p>
            """
        })
        print("✅ Email sent successfully")

    except Exception as e:
        print("❌ Email error:", str(e))

# -------- TEST ROUTE --------
@app.route('/test')
def test():
    return "✅ WORKING"

# -------- EMAIL TEST ROUTE --------
@app.route('/send-test')
def send_test():
    try:
        resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": ["masountajinder@gmail.com"],
            "subject": "TEST EMAIL",
            "html": "<h1>Email Working ✅</h1>"
        })
        return "✅ Email Sent Successfully"
    except Exception as e:
        return f"❌ Error: {str(e)}"

# -------- CHECK --------
@app.route('/check')
def check():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM complaints")
    count = c.fetchone()[0]
    conn.close()
    return jsonify({"count": count})

# -------- LANDING --------
@app.route('/')
def landing():
    return render_template("landing.html")

# -------- COMPLAINT --------
@app.route('/complaint', methods=['GET', 'POST'])
def complaint():
    if request.method == 'POST':
        try:
            complaint_id = "CMP" + str(random.randint(10000, 99999))

            data = (
                complaint_id,
                request.form.get('name'),
                request.form.get('address'),
                request.form.get('contact'),
                request.form.get('email'),
                request.form.get('unit'),
                request.form.get('wo'),
                request.form.get('quarter'),
                request.form.get('complaint')
            )

            conn = sqlite3.connect("database.db")
            c = conn.cursor()
            c.execute("""
                INSERT INTO complaints 
                (complaint_id, name, address, contact, email, unit, wo, quarter, complaint)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, data)
            conn.commit()
            conn.close()

            send_email(data)

            return f"✅ Complaint Submitted! Your ID: {complaint_id}"

        except Exception as e:
            print("❌ Submit error:", str(e))
            return f"Error: {str(e)}"

    return render_template("complaint.html")

# -------- TRACK --------
@app.route('/track', methods=['GET', 'POST'])
def track():
    if request.method == 'POST':
        cid = request.form.get('cid')

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM complaints WHERE complaint_id=?", (cid,))
        data = c.fetchone()
        conn.close()

        return render_template("track.html", data=data)

    return render_template("track.html")

# -------- LOGIN --------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('username') == "admin" and request.form.get('password') == "1234":
            session['admin'] = True
            return redirect('/admin')
        return "❌ Wrong Username or Password"
    return render_template("login.html")

# -------- ADMIN --------
@app.route('/admin')
def admin():
    if not session.get('admin'):
        return redirect('/login')

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM complaints")
    data = c.fetchall()
    conn.close()

    return render_template("admin.html", data=data)

# -------- LOGOUT --------
@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect('/login')

# -------- REPLY --------
@app.route('/reply/<cid>', methods=['POST'])
def reply(cid):
    if not session.get('admin'):
        return redirect('/login')

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("UPDATE complaints SET reply=? WHERE complaint_id=?",
              (request.form.get('reply'), cid))
    conn.commit()
    conn.close()

    return redirect('/admin')

# -------- RUN --------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)