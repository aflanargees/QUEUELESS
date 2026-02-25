from flask import Flask, render_template, request, jsonify, session,redirect
import sqlite3,random

app = Flask(__name__)
app.secret_key = "supersecretkey"


# -------------------- DATABASE --------------------
def get_db():
    conn = sqlite3.connect("queueless.db")
    conn.row_factory = sqlite3.Row
    return conn


def create_master_tables():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS districts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            district_name TEXT UNIQUE
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS panchayats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            district_id INTEGER,
            panchayat_name TEXT,
            FOREIGN KEY (district_id) REFERENCES districts(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS wards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            panchayat_id INTEGER,
            ward_name TEXT,
            FOREIGN KEY (panchayat_id) REFERENCES panchayats(id)
        )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS panchayat_admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        panchayat_id INTEGER,
        FOREIGN KEY (panchayat_id) REFERENCES panchayats(id)
    )
""")

    conn.commit()
    conn.close()


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            district TEXT,
            panchayat TEXT,
            ward TEXT,
            purpose TEXT,
            token_number INTEGER,
            counter_number INTEGER,
            status TEXT,
            panchayat_id INTEGER,
            FOREIGN KEY (panchayat_id) REFERENCES panchayats(id)
        )
    """)
    conn.commit()
    conn.close()
def seed_data_if_empty():
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM districts").fetchone()[0]

    if count == 0:
        print("Seeding master data...")
        import import_data  # this runs your import script

    conn.close()

create_master_tables()
init_db()
seed_data_if_empty()


# -------------------- ROUTES --------------------
@app.route("/")
def welcome():
    return render_template("welcome.html")


@app.route("/user")
def user():

    if not session.get("logged_in"):
        return redirect("/")

    conn = get_db()
    districts = conn.execute(
        "SELECT id, district_name FROM districts ORDER BY district_name"
    ).fetchall()
    conn.close()

    return render_template("user.html", districts=districts)

@app.route("/send_otp", methods=["POST"])
def send_otp():

    data = request.json
    phone = data["phone"]

    otp = str(random.randint(1000, 9999))

    session["login_phone"] = phone
    session["login_otp"] = otp

    print("Demo OTP:", otp)  # check terminal

    return jsonify({
    "status": "sent",
    "otp": otp
})



@app.route("/verify_login_otp", methods=["POST"])
def verify_login_otp():
    data = request.json
    user_otp = data["otp"]

    print("Entered OTP:", user_otp)
    print("Session OTP:", session.get("login_otp"))

    if "login_otp" in session and user_otp == session["login_otp"]:
        session["logged_in"] = True
        session.pop("login_otp", None)

        print("Login Success ✅")
        return jsonify({"status": "success"})

    print("Login Failed ❌")
    return jsonify({"status": "failed"})


# -------------------- GET PANCHAYATS --------------------
@app.route("/get_panchayats/<path:district>")
def get_panchayats(district):
    conn = get_db()
    rows = conn.execute("""
        SELECT panchayat_name
        FROM panchayats
        JOIN districts ON panchayats.district_id = districts.id
        WHERE districts.district_name = ?
        ORDER BY panchayat_name
    """, (district,)).fetchall()
    conn.close()
    return jsonify([r["panchayat_name"] for r in rows])


# -------------------- GET WARDS --------------------
@app.route("/get_wards/<path:panchayat>")
def get_wards(panchayat):
    conn = get_db()
    rows = conn.execute("""
        SELECT ward_name
        FROM wards
        JOIN panchayats ON wards.panchayat_id = panchayats.id
        WHERE panchayats.panchayat_name = ?
        ORDER BY CAST(SUBSTR(ward_name, 6) AS INTEGER)
    """, (panchayat,)).fetchall()
    conn.close()
    return jsonify([r["ward_name"] for r in rows])


# -------------------- GENERATE TOKEN --------------------
@app.route("/generate_token", methods=["POST"])
def generate_token():

    data = request.json
    conn = get_db()

    # Check existing waiting token
    existing = conn.execute("""
        SELECT token_number, counter_number 
        FROM tokens 
        WHERE name=? AND status='waiting'
    """, (data["name"],)).fetchone()

    if existing:
        session["user_token"] = existing["token_number"]
        session["user_counter"] = existing["counter_number"]
        conn.close()
        return jsonify({
            "message": "Token already generated",
            "token": existing["token_number"],
            "counter": existing["counter_number"]
        })

    # Get next token
    last_token = conn.execute(
        "SELECT MAX(token_number) FROM tokens"
    ).fetchone()[0]

    token_no = 1 if last_token is None else last_token + 1

    # Counter round-robin 1–3
    last_counter = conn.execute(
        "SELECT MAX(counter_number) FROM tokens"
    ).fetchone()[0]

    counter_no = 1 if last_counter is None else (1 if last_counter == 3 else last_counter + 1)

    # Get panchayat_id
    row = conn.execute(
        "SELECT id FROM panchayats WHERE TRIM(LOWER(panchayat_name)) = TRIM(LOWER(?))",
        (data["panchayat"],)
    ).fetchone()

    if row is None:
        return jsonify({"error": "Invalid panchayat!"}), 400

    panchayat_id = row[0]

    # INSERT TOKEN
    conn.execute("""
        INSERT INTO tokens (name, district, panchayat, ward, purpose,
            token_number, counter_number, status, panchayat_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["name"],
        data["district"],
        data["panchayat"],
        data["ward"],
        data["purpose"],
        token_no,
        counter_no,
        "waiting",
        panchayat_id
    ))

    session["user_token"] = token_no
    session["user_counter"] = counter_no

    conn.commit()
    conn.close()

    return jsonify({
        "token": token_no,
        "counter": counter_no
    })
# -------------------- ADMIN --------------------
@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect("/admin/login")

    p_id = session["panchayat_id"]

    conn = get_db()

    # 🔥 GET PANCHAYAT NAME
    pname = conn.execute("SELECT panchayat_name FROM panchayats WHERE id=?", (p_id,)).fetchone()[0]

    tokens = conn.execute("""
        SELECT * FROM tokens WHERE panchayat_id=?
    """, (p_id,)).fetchall()

    conn.close()

    return render_template("admin.html", tokens=tokens, panchayat_name=pname)

@app.route("/admin/table_reload")
def table_reload():
    if not session.get("admin"):
        return ""

    p_id = session["panchayat_id"]

    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM tokens WHERE panchayat_id=? ORDER BY id DESC",
        (p_id,)
    ).fetchall()
    conn.close()

    return render_template("admin_table.html", tokens=rows)

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()

        # Check admin credentials
        cur.execute("SELECT * FROM panchayat_admins WHERE username=? AND password=?", 
                    (username, password))
        admin = cur.fetchone()

        if admin:
            # Store admin session + panchayat_id
            session["admin"] = True
            session["panchayat_id"] = admin["panchayat_id"]
            return redirect("/admin/dashboard")
        else:
            return "Invalid login bro"

    return render_template("admin_login.html")


@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.pop("admin", None)
    session.pop("panchayat_id", None)
    return redirect("/admin/login")

# -------------------- TOKEN ACTIONS --------------------
@app.route("/serve_token/<int:tno>")
def serve_token(tno):
    conn = get_db()
    conn.execute(
        "UPDATE tokens SET status='serving' WHERE token_number=?",
        (tno,)
    )
    conn.commit()
    conn.close()
    return "OK"

@app.route("/done_token/<int:tno>")
def done_token(tno):
    conn = get_db()

    conn.execute(
        "DELETE FROM tokens WHERE token_number=?",
        (tno,)
    )

    conn.commit()
    conn.close()
    return "OK"


@app.route("/cancel_token/<int:tno>")
def cancel_token(tno):
    conn = get_db()
    conn.execute("DELETE FROM tokens WHERE token_number=?", (tno,))
    conn.commit()
    conn.close()
    return "OK"


# -------------------- LIVE STATUS --------------------
@app.route("/user/status")
def user_status():
    token = session.get("user_token")
    counter = session.get("user_counter")

    return render_template(
        "user_status.html",
        user_token=token,
        user_counter=counter
    )

@app.route("/live_data")
def live_data():
    conn = get_db()

    # serving tokens (correct lowercase)
    serving = conn.execute(
        "SELECT token_number, counter_number FROM tokens WHERE status='serving'"
    ).fetchall()

    # waiting tokens
    waiting = conn.execute(
        "SELECT COUNT(*) FROM tokens WHERE status='waiting'"
    ).fetchone()[0]

    conn.close()

    serving_list = [
        {"token": row["token_number"], "counter": row["counter_number"]}
        for row in serving
    ]

    return jsonify({
        "serving_list": serving_list,
        "waiting_count": waiting
    })


@app.route("/live_data/<int:counter_no>")
def live_data_counter(counter_no):
    conn = get_db()

    serving = conn.execute(
        "SELECT token_number FROM tokens WHERE status='serving' AND counter_number=?",
        (counter_no,)
    ).fetchone()

    conn.close()

    return jsonify({
        "token": serving["token_number"] if serving else None
    })

@app.route("/all_tokens")
def all_tokens():
    conn = get_db()
    rows = conn.execute(
        "SELECT token_number, counter_number FROM tokens ORDER BY token_number"
    ).fetchall()
    conn.close()

    return jsonify([
        {"token": r["token_number"], "counter": r["counter_number"]} 
        for r in rows
    ])

@app.route("/serve/<int:panchayat_id>", methods=["POST"])
def serve_next(panchayat_id):
    conn = get_db()
    cur = conn.cursor()

    # 1) Clear previous serving token
    cur.execute("""
        UPDATE tokens SET status='done'
        WHERE status='serving' AND panchayat_id=?
    """, (panchayat_id,))

    # 2) Get next waiting token
    cur.execute("""
        SELECT id, token_number FROM tokens
        WHERE status='waiting' AND panchayat_id=?
        ORDER BY id ASC
        LIMIT 1
    """, (panchayat_id,))
    next_token = cur.fetchone()

    if next_token:
        token_id = next_token["id"]

        # Mark as serving
        cur.execute("""
            UPDATE tokens SET status='serving'
            WHERE id=?
        """, (token_id,))
        conn.commit()
        serving_number = next_token["token_number"]
    else:
        serving_number = None  # No token

    conn.close()

    return redirect("/admin/dashboard")

@app.route("/user/services")
def user_services():
    return render_template("services.html")


@app.route("/user/help")
def user_help():
    return render_template("help.html")

@app.route("/reset_token")
def reset_token():
    session.pop("user_token", None)
    session.pop("user_counter", None)
    return "OK"

# -------------------- DISPLAY PAGE PER COUNTER --------------------
@app.route("/display/<int:counter_no>")
def display(counter_no):
    if not session.get("admin"):
        return redirect("/admin/login")

    p_id = session["panchayat_id"]

    conn = get_db()
    tokens = conn.execute("""
        SELECT *
        FROM tokens
        WHERE counter_number=? AND panchayat_id=?
        ORDER BY id DESC
    """, (counter_no, p_id)).fetchall()

    conn.close()

    return render_template("display.html", tokens=tokens, counter_no=counter_no)

@app.route("/display_reload/<int:counter_no>")
def display_reload(counter_no):
    if not session.get("admin"):
        return ""

    p_id = session["panchayat_id"]

    conn = get_db()
    tokens = conn.execute("""
        SELECT *
        FROM tokens
        WHERE counter_number=? AND panchayat_id=?
        ORDER BY id DESC
    """, (counter_no, p_id)).fetchall()

    conn.close()

    return render_template("display_rows.html", tokens=tokens)



if __name__ == "__main__":
    app.run(debug=True)

