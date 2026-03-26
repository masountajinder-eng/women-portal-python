from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

# DATABASE INIT
def init_db():
    conn = sqlite3.connect('complaints.db')
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        mobile TEXT,
        unit TEXT,
        email TEXT,
        relation TEXT,
        qtr TEXT,
        address TEXT,
        complaint TEXT,
        reply TEXT
    )
    ''')

    conn.commit()
    conn.close()

init_db()

# HOME PAGE
@app.route('/')
def home():
    return render_template('index.html')

# SUBMIT FORM
@app.route('/submit', methods=['POST'])
def submit():
    data = (
        request.form['name'],
        request.form['mobile'],
        request.form['unit'],
        request.form['email'],
        request.form['relation'],
        request.form['qtr'],
        request.form['address'],
        request.form['complaint'],
        ""
    )

    conn = sqlite3.connect('complaints.db')
    c = conn.cursor()

    c.execute('''
    INSERT INTO complaints (name, mobile, unit, email, relation, qtr, address, complaint, reply)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', data)

    conn.commit()
    conn.close()

    return "Complaint Submitted Successfully <br><a href='/'>Go Back</a> | <a href='/view'>View Complaints</a>"

# VIEW USER
@app.route('/view')
def view():
    conn = sqlite3.connect('complaints.db')
    c = conn.cursor()
    c.execute("SELECT * FROM complaints")
    rows = c.fetchall()
    conn.close()
    return render_template('view.html', rows=rows)

# ADMIN LOGIN
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == '1234':
            session['admin'] = True
            return redirect('/dashboard')
    return render_template('admin.html')

# ADMIN DASHBOARD
@app.route('/dashboard')
def dashboard():
    if 'admin' not in session:
        return redirect('/admin')

    conn = sqlite3.connect('complaints.db')
    c = conn.cursor()
    c.execute("SELECT * FROM complaints")
    rows = c.fetchall()
    conn.close()

    return render_template('dashboard.html', rows=rows)

# REPLY SYSTEM
@app.route('/reply/<int:id>', methods=['POST'])
def reply(id):
    if 'admin' not in session:
        return redirect('/admin')

    reply_text = request.form['reply']

    conn = sqlite3.connect('complaints.db')
    c = conn.cursor()
    c.execute("UPDATE complaints SET reply=? WHERE id=?", (reply_text, id))
    conn.commit()
    conn.close()

    return redirect('/dashboard')

# RUN
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=10000, debug=True)