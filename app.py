from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
import os
from dotenv import load_dotenv
import resend
import random
import base64

load_dotenv()

app = Flask(__name__)
app.secret_key = "secret123"

resend.api_key = os.environ.get("RESEND_API_KEY")

print("🔥 FINAL ULTRA PRO CODE RUNNING")

# ✅ PATHS
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static/audio")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
            complaint TEXT,
            category TEXT,
            subcategory TEXT,
            reply TEXT,
            audio TEXT
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# -------- EMAIL --------
def send_email(data, audio_link=None):
    try:
        audio_html = ""
        if audio_link:
            audio_html = f'<p><b>Audio:</b> <a href="{audio_link}">Listen</a></p>'

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
                {audio_html}
            """
        })

        print("✅ Email sent")

    except Exception as e:
        print("❌ Email error:", str(e))


# -------- ROUTES --------

@app.route('/')
def landing():
    return render_template("landing.html")


# ✅ COMPLAINT SUBMIT
@app.route('/complaint', methods=['GET', 'POST'])
def complaint():
    if request.method == 'POST':
        try:
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

            # 🎤 AUDIO SAVE
            audio_data = request.form.get("audio")
            audio_path = ""

            if audio_data:
                try:
                    header, encoded = audio_data.split(",", 1)
                    file_data = base64.b64decode(encoded)

                    filename = f"{complaint_id}.webm"
                    filepath = os.path.join(UPLOAD_FOLDER, filename)

                    with open(filepath, "wb") as f:
                        f.write(file_data)

                    audio_path = f"/static/audio/{filename}"

                except Exception as e:
                    print("❌ Audio error:", str(e))

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()

            c.execute("""
                INSERT INTO complaints 
                (complaint_id, name, address, contact, email, unit, wo, quarter, complaint, category, subcategory, reply, audio)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                complaint_id, name, address, contact, email,
                unit, wo, quarter, complaint_text,
                category, subcategory, "", audio_path
            ))

            conn.commit()
            conn.close()

            send_email((
                complaint_id, name, address, contact, email,
                unit, wo, quarter, category, subcategory, complaint_text
            ), audio_path)

            return jsonify({
                "status": "success",
                "id": complaint_id
            })

        except Exception as e:
            return jsonify({
                "status": "error",
                "message": str(e)
            })

    return render_template("complaint.html")


# ✅ 🔥 TRACK SYSTEM (NEW ADD)
@app.route('/track', methods=['GET', 'POST'])
def track():
    data = None

    if request.method == 'POST':
        cid = request.form.get('complaint_id')

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute("SELECT * FROM complaints WHERE complaint_id=?", (cid,))
        data = c.fetchone()

        conn.close()

    return render_template("track.html", data=data)


# ✅ ADMIN PANEL
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


@app.route('/check')
def check():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM complaints")
    count = c.fetchone()[0]
    conn.close()

    return jsonify({"count": count})


# ✅ LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('username') == "admin" and request.form.get('password') == "1234":
            session['admin'] = True
            return redirect('/admin')
        return "❌ Wrong Username or Password"
    return render_template("login.html")


@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect('/login')


# ✅ REPLY
@app.route('/reply/<cid>', methods=['POST'])
def reply(cid):
    if not session.get('admin'):
        return jsonify({"status": "error", "message": "Unauthorized"})

    reply_text = request.form.get('reply')

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute("UPDATE complaints SET reply=? WHERE complaint_id=?",
                  (reply_text, cid))

        conn.commit()
        conn.close()

        return jsonify({"status": "success"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


# -------- RUN --------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)