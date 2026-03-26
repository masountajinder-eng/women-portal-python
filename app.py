from flask import Flask, render_template, request, redirect
import sqlite3
import os
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# -------- DATABASE --------
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            mobile TEXT,
            address TEXT,
            unit TEXT,
            complaint TEXT,
            email TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# -------- HOME --------
@app.route('/')
def index():
    return render_template('index.html')

# -------- SUBMIT --------
@app.route('/submit', methods=['POST'])
def submit():
    name = request.form.get('name')
    mobile = request.form.get('mobile')
    address = request.form.get('address')
    unit = request.form.get('unit')
    complaint = request.form.get('complaint')
    email = request.form.get('email')

    # SAVE DATA
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO complaints (name, mobile, address, unit, complaint, email)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, mobile, address, unit, complaint, email))
    conn.commit()
    conn.close()

    # -------- EMAIL --------
    try:
        sender_email = "masountajinder@gmail.com"
        receiver_email = "masountajinder@gmail.com"
        password = "uweb itvc itxm pbhi"

        msg = MIMEText(f"""
New Complaint:

Name: {name}
Mobile: {mobile}
Address: {address}
Unit: {unit}
Complaint: {complaint}
Email: {email}
""")

        msg['Subject'] = "New Complaint Received"
        msg['From'] = sender_email
        msg['To'] = receiver_email

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()

        print("Email sent")

    except Exception as e:
        print("Email error:", e)

    return redirect('/')

# -------- VIEW --------
@app.route('/view')
def view():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM complaints")
    data = cursor.fetchall()
    conn.close()

    return render_template('view.html', data=data)

# -------- RUN --------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))