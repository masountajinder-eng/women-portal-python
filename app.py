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
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            mobile TEXT
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
    name = request.form['name']
    mobile = request.form['mobile']

    # Save to DB
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (name, mobile) VALUES (?, ?)", (name, mobile))
    conn.commit()
    conn.close()

    # -------- EMAIL SEND --------
    try:
        sender_email = "masountajinder@gmail.com"
        receiver_email = "masountajinder@gmail.com"
        password = "abcd efgh ijkl mnop"

        msg = MIMEText(f"New Entry:\n\nName: {name}\nMobile: {mobile}")
        msg['Subject'] = "New Form Submission"
        msg['From'] = sender_email
        msg['To'] = receiver_email

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()

        print("Email sent successfully")

    except Exception as e:
        print("Email error:", e)

    return redirect('/')

# -------- VIEW --------
@app.route('/view')
def view():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    data = cursor.fetchall()
    conn.close()

    return render_template('view.html', data=data)

# -------- RUN (Render compatible) --------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))