from flask import Flask, render_template, request, redirect
import sqlite3
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

# ---------------- DATABASE SETUP ----------------
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        address TEXT,
        pincode TEXT,
        complaint TEXT,
        email TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------- HOME PAGE ----------------
@app.route("/")
def home():
    return render_template("index.html")

# ---------------- SUBMIT FORM ----------------
@app.route("/submit", methods=["POST"])
def submit():
    try:
        name = request.form["name"]
        phone = request.form["phone"]
        address = request.form["address"]
        pincode = request.form["pincode"]
        complaint = request.form["complaint"]
        email = request.form["email"]

        # -------- SAVE TO DATABASE --------
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO complaints (name, phone, address, pincode, complaint, email)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (name, phone, address, pincode, complaint, email))
        conn.commit()
        conn.close()

        print("Data saved successfully")

        # -------- SEND EMAIL --------
        try:
            sender_email = "masountajinder@gmail.com"
            receiver_email = "masountajinder@gmail.com"
            password = "uwebitvcitxmpbhi"

            msg = MIMEText(f"""
New Complaint Received:

Name: {name}
Phone: {phone}
Address: {address}
Pincode: {pincode}
Complaint: {complaint}
Email: {email}
""")

            msg['Subject'] = "New Complaint"
            msg['From'] = sender_email
            msg['To'] = receiver_email

            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender_email, password)
            server.send_message(msg)
            server.quit()

            print("Email sent successfully")

        except Exception as e:
            print("Email error:", e)

        return redirect("/")

    except Exception as e:
        print("Submit error:", e)
        return "Internal Server Error"

# ---------------- VIEW DATA ----------------
@app.route("/view")
def view():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM complaints")
    data = cursor.fetchall()
    conn.close()
    return render_template("view.html", data=data)

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run()