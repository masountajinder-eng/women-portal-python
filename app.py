from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
import os
from dotenv import load_dotenv
import resend
import random

load_dotenv()

app = Flask(__name__)
app.secret_key = "secret123"

# ✅ RESEND KEY
resend.api_key = os.environ.get("RESEND_API_KEY")

print("🔥 FINAL FULLY FIXED CODE RUNNING")

# ✅ DB PATH FIX (VERY IMPORTANT FOR RENDER)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

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
            category TEXT,
            subcategory TEXT,
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
            "from": "onboarding@resend.dev",
            "to": ["masountajinder@gmail.com"],
            "subject": f"🚨 New Complaint {data[0]}",
            "html": f"""
                <h2>New Complaint Submitted</h2>
                <p><b>ID:</b> {data[0]}</p>
                <p><b>Name:</b> {data[1]}</p>
                <p><b>Email:</b> {data[4]}</p>
                <p><b>Contact:</b> {data[3]}</p>
                <p><b>Category:</b> {data[8]}</p>
                <p><b>Subcategory:</b> {data[9]}</p>
                <p><b>Complaint:</b><br>{data[10]}</p>
            """
        })
        print("✅ Email sent")

    except Exception as e:
        print("❌ Email error:", str(e))


# -------- TEST --------
@app.route('/test')
def test():
    return "✅ WORKING"


# -------- CHECK --------
@app.route('/check')
def check():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM complaints")
    count = c.fetchone()[0]
    conn.close()
    return jsonify({"count": count})


# -------- LANDING --------
@app.route('/')
def landing():
    return render_template("landing.html")


# -------- 🔥 COMPLAINT --------
@app.route('/complaint', methods=['GET', 'POST'])
def complaint():
    if request.method == 'POST':
        try:
            print("📥 FORM DATA:", request.form)

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

            print("📌 CATEGORY:", category)
            print("📌 SUBCATEGORY:", subcategory)

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()

            c.execute("""
                INSERT INTO complaints 
                (complaint_id, name, address, contact, email, unit, wo, quarter, category, subcategory, complaint)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                complaint_id, name, address, contact, email,
                unit, wo, quarter, category, subcategory, complaint_text
            ))

            conn.commit()
            conn.close()

            print("✅ SAVED IN DATABASE")

            # email
            send_email((
                complaint_id, name, address, contact, email,
                unit, wo, quarter, category, subcategory, complaint_text
            ))

            return jsonify({
                "status": "success",
                "id": complaint_id
            })

        except Exception as e:
            print("❌ ERROR:", str(e))
            return jsonify({
                "status": "error",
                "message": str(e)
            })

    return render_template("complaint.html")


# -------- TRACK --------
@app.route('/track', methods=['GET', 'POST'])
def track():
    if request.method == 'POST':
        cid = request.form.get('cid')

        conn = sqlite3.connect(DB_PATH)
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

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM complaints ORDER BY id DESC")
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

    conn = sqlite3.connect(DB_PATH)
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