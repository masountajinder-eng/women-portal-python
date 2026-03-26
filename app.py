from flask import Flask, render_template, request, redirect
import sqlite3
import os
from dotenv import load_dotenv
import resend
import random

load_dotenv()

app = Flask(__name__)

resend.api_key = os.environ.get("RESEND_API_KEY")

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

# -------- LANDING --------
@app.route('/')
def landing():
    return render_template("landing.html")

# -------- FORM --------
@app.route('/complaint')
def complaint():
    return render_template("complaint.html")

# -------- SUBMIT --------
@app.route('/submit', methods=['POST'])
def submit():
    complaint_id = "CMP" + str(random.randint(10000, 99999))

    data = (
        complaint_id,
        request.form['name'],
        request.form['address'],
        request.form['contact'],
        request.form['email'],
        request.form['unit'],
        request.form['wo'],
        request.form['quarter'],
        request.form['complaint']
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

    # EMAIL TO ADMIN
    resend.Emails.send({
        "from": "onboarding@resend.dev",
        "to": "your_admin_email@gmail.com",
        "subject": "🚨 New Complaint",
        "html": f"<h3>New Complaint ID: {complaint_id}</h3><p>{data}</p>"
    })

    return f"✅ Complaint Submitted! Your ID: {complaint_id}"

# -------- TRACK --------
@app.route('/track', methods=['GET', 'POST'])
def track():
    if request.method == 'POST':
        cid = request.form['cid']
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM complaints WHERE complaint_id=?", (cid,))
        data = c.fetchone()
        conn.close()
        return render_template("track.html", data=data)

    return render_template("track.html")

# -------- ADMIN --------
@app.route('/admin')
def admin():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM complaints")
    data = c.fetchall()
    conn.close()
    return render_template("admin.html", data=data)

# -------- REPLY --------
@app.route('/reply/<cid>', methods=['POST'])
def reply(cid):
    reply_text = request.form['reply']

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("UPDATE complaints SET reply=? WHERE complaint_id=?", (reply_text, cid))
    conn.commit()
    conn.close()

    return redirect('/admin')

# -------- RUN --------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)