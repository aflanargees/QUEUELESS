from flask import Flask, render_template, request, jsonify
import sqlite3
import random

print("=== THIS APP.PY IS RUNNING ===")

app = Flask(__name__)

# ---------- DATABASE SETUP ----------
def get_db_connection():
    conn = sqlite3.connect("queueless.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            district TEXT,
            panchayat TEXT,
            ward INTEGER,
            purpose TEXT,
            token_number INTEGER,
            counter_number INTEGER,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------- ROUTES ----------
@app.route("/")
def welcome():
    return render_template("welcome.html")

@app.route("/user")
def user():
    return render_template("user.html")

@app.route("/admin")
def admin():
    conn = get_db_connection()
    tokens = conn.execute("""
        SELECT token_number, counter_number, name, district,
               panchayat, ward, purpose, status
        FROM tokens
        ORDER BY id DESC
    """).fetchall()
    conn.close()
    return render_template("admin.html", tokens=tokens)

# ---------- TOKEN GENERATION ----------
@app.route("/generate_token", methods=["POST"])
def generate_token():
    data = request.json

    token_number = random.randint(1, 100)
    counter_number = random.randint(1, 5)

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO tokens
        (name, district, panchayat, ward, purpose,
         token_number, counter_number, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["name"],
        data["district"],
        data["panchayat"],
        data["ward"],
        data["purpose"],
        token_number,
        counter_number,
        "Waiting"
    ))
    conn.commit()
    conn.close()

    return jsonify({
        "token": token_number,
        "counter": counter_number
    })

# ---------- SERVE TOKEN (PHASE 3.5) ----------
@app.route("/serve_token/<int:token_no>")
def serve_token(token_no):
    conn = get_db_connection()

    # Reset all tokens to Waiting
    conn.execute("UPDATE tokens SET status='Waiting'")

    # Set selected token to Serving
    conn.execute(
        "UPDATE tokens SET status='Serving' WHERE token_number=?",
        (token_no,)
    )

    conn.commit()
    conn.close()

    print("Serving token:", token_no)
    return "OK"

@app.route("/done_token/<int:token_no>")
def done_token(token_no):
    conn = get_db_connection()

    conn.execute(
        "UPDATE tokens SET status='Done' WHERE token_number=?",
        (token_no,)
    )

    conn.commit()
    conn.close()

    print("Token completed:", token_no)
    return "OK"

# ---------- RUN APP (MUST BE LAST) ----------
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
