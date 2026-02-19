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
            status TEXT
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

    # 🔥 Check if same name already has waiting token
    existing = conn.execute("""
        SELECT token_number, counter_number 
        FROM tokens 
        WHERE name=? AND status='Waiting'
    """, (data["name"],)).fetchone()

    if existing:
        conn.close()
        return jsonify({
            "message": "Token already generated",
            "token": existing["token_number"],
            "counter": existing["counter_number"]
        })

    # 🔹 Get next token number
    last_token = conn.execute(
        "SELECT MAX(token_number) FROM tokens"
    ).fetchone()[0]

    token_no = 1 if last_token is None else last_token + 1

    # 🔹 Assign counter in round-robin (1,2,3)
    last_counter = conn.execute(
        "SELECT MAX(counter_number) FROM tokens"
    ).fetchone()[0]

    if last_counter is None:
        counter_no = 1
    else:
        counter_no = 1 if last_counter == 3 else last_counter + 1

    conn.execute("""
        INSERT INTO tokens (name, district, panchayat, ward, purpose,
            token_number, counter_number, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["name"], data["district"], data["panchayat"],
        data["ward"], data["purpose"],
        token_no, counter_no, "Waiting"
    ))

    conn.commit()
    conn.close()

    return jsonify({
        "token": token_no,
        "counter": counter_no
    })


# -------------------- ADMIN --------------------
@app.route("/admin")
def admin():

    if not session.get("logged_in"):
        return redirect("/")

    conn = get_db()
    rows = conn.execute("SELECT * FROM tokens ORDER BY id DESC").fetchall()
    conn.close()

    return render_template("admin.html", tokens=rows)


@app.route("/admin/table_reload")
def table_reload():
    conn = get_db()
    rows = conn.execute("SELECT * FROM tokens ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("admin_table.html", tokens=rows)


# -------------------- TOKEN ACTIONS --------------------
@app.route("/serve_token/<int:tno>")
def serve_token(tno):
    conn = get_db()

    conn.execute(
        "UPDATE tokens SET status='Serving' WHERE token_number=?",
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

    serving = conn.execute(
        "SELECT token_number, counter_number FROM tokens WHERE status='Serving'"
    ).fetchall()

    waiting = conn.execute(
        "SELECT COUNT(*) FROM tokens WHERE status='Waiting'"
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
        "SELECT token_number FROM tokens WHERE status='Serving' AND counter_number=?",
        (counter_no,)
    ).fetchone()

    conn.close()

    token = serving["token_number"] if serving else None

    return jsonify({
        "token": token
    })



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
    conn = get_db()

    tokens = conn.execute("""
        SELECT * FROM tokens
        WHERE counter_number=?
        ORDER BY id DESC
    """, (counter_no,)).fetchall()

    conn.close()

    return render_template(
        "display.html",
        tokens=tokens,
        counter_no=counter_no
    )


@app.route("/display_reload/<int:counter_no>")
def display_reload(counter_no):
    conn = get_db()

    tokens = conn.execute("""
        SELECT * FROM tokens
        WHERE counter_number=?
        ORDER BY id DESC
    """, (counter_no,)).fetchall()

    conn.close()

    return render_template("display_rows.html", tokens=tokens)


if __name__ == "__main__":
    app.run(debug=True)

