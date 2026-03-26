from flask import Flask, render_template, request
import sqlite3
import os
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# ---------------- DATABASE INIT ----------------
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            message TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ---------------- EMAIL FUNCTION ----------------
def send_email(name, email, message):
    try:
        sender_email = "masountajinder@gmail.com"        # 👈 apna gmail
        sender_password = "uwebitvcitxmpbhi"      # 👈 Gmail App Password

        receiver_email = "masountajinder@gmail.com"     # 👈 admin email

        subject = "New Form Submission"
        body = f"""
Name: {name}
Email: {email}
Message: {message}
"""

        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = receiver_email

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()

        print("✅ Email sent successfully")

    except Exception as e:
        print("❌ Email error:", e)


# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template('index.html')


# ---------------- SUBMIT ----------------
@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            email = request.form.get('email')
            message = request.form.get('message')

            # SAVE TO DATABASE
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            c.execute("INSERT INTO messages (name, email, message) VALUES (?, ?, ?)",
                      (name, email, message))
            conn.commit()
            conn.close()

            # SEND EMAIL
            send_email(name, email, message)

            return """
            <h2>✅ Data Saved + Email Sent!</h2>
            <a href="/">⬅ Back</a>
            """

        except Exception as e:
            return f"❌ Error: {str(e)}"

    return "⚠️ Please submit form from homepage"


# ---------------- ADMIN PANEL ----------------
@app.route('/admin')
def admin():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM messages")
    data = c.fetchall()
    conn.close()

    return render_template('admin.html', data=data)


# ---------------- RUN ----------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
    import resend

resend.api_key = "re_i5UKKcEF_6o9QywHvtjExCvUP462dGuG2"