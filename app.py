from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3, random

app = Flask(__name__)
app.secret_key = "supersecretkey"


# ---------------- DATABASE ----------------
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

    # ⭐ CREATE COUNTERS TABLE (MISSING BEFORE)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS counters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            counter_number INTEGER,
            is_active INTEGER DEFAULT 0
        )
    """)

    conn.commit()

    # Insert default counters if empty
    count = conn.execute("SELECT COUNT(*) FROM counters").fetchone()[0]
    if count == 0:
        conn.execute("INSERT INTO counters(counter_number, is_active) VALUES (1, 0)")
        conn.execute("INSERT INTO counters(counter_number, is_active) VALUES (2, 0)")
        conn.execute("INSERT INTO counters(counter_number, is_active) VALUES (3, 0)")
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
        print("Seeding master data…")
        import import_data
    conn.close()


create_master_tables()
init_db()
seed_data_if_empty()


# ---------------- USER PAGES ----------------
@app.route("/")
def welcome():
    return render_template("welcome.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/user")
def user():
    if not session.get("logged_in"):
        return redirect("/")
    conn = get_db()
    districts = conn.execute("SELECT id, district_name FROM districts").fetchall()
    conn.close()
    return render_template("user.html", districts=districts)


@app.route("/user/status")
def user_status():
    if not session.get("logged_in"):
        return redirect("/")

    user_token = session.get("user_token")
    user_counter = session.get("user_counter")

    print("TOKEN:", user_token)      # DEBUG
    print("COUNTER:", user_counter)  # DEBUG

    return render_template(
        "user_status.html",
        user_token=user_token,
        user_counter=user_counter
    )

@app.route("/services")
def services():
    return render_template("services.html")


@app.route("/user/services")
def user_services():
    return render_template("services.html")


@app.route("/live_status")
def live_status():
    conn = get_db()
    rows = conn.execute("SELECT * FROM tokens ORDER BY token_number DESC").fetchall()
    conn.close()
    return render_template("display_table.html", tokens=rows)


@app.route("/help")
def help_page():
    return render_template("help.html")


@app.route("/user/help")
def user_help():
    return render_template("help.html")


# ---------------- OTP LOGIN ----------------
@app.route("/send_otp", methods=["POST"])
def send_otp():
    data = request.json
    otp = str(random.randint(1000, 9999))
    session["login_phone"] = data["phone"]
    session["login_otp"] = otp
    print("OTP:", otp)
    return jsonify({"status": "sent", "otp": otp})


@app.route("/verify_login_otp", methods=["POST"])
def verify_login_otp():
    if request.json["otp"] == session.get("login_otp"):
        session["logged_in"] = True
        session.pop("login_otp", None)
        return jsonify({"status": "success"})
    return jsonify({"status": "failed"})


# ---------------- TOKEN GENERATION ----------------
@app.route("/generate_token", methods=["POST"])
def generate_token():
    data = request.json
    conn = get_db()

    # ⭐ CHECK DUPLICATE TOKEN (same name in same panchayat still waiting)
    existing = conn.execute("""
        SELECT token_number, counter_number
        FROM tokens
        WHERE name=? AND district=? AND panchayat=? AND status='waiting'
    """, (data["name"], data["district"], data["panchayat"])).fetchone()

    if existing:
        session["user_token"] = existing["token_number"]
        session["user_counter"] = existing["counter_number"]

        return jsonify({
            "duplicate": True,
            "token_number": existing["token_number"],
            "counter_number": existing["counter_number"]
        })

    # ⭐ GET PANCHAYAT ID FIRST (IMPORTANT)
    p_row = conn.execute(
        "SELECT id FROM panchayats WHERE TRIM(LOWER(panchayat_name)) = TRIM(LOWER(?))",
        (data["panchayat"],)
    ).fetchone()

    if not p_row:
        conn.close()
        return jsonify({"error": "Invalid panchayat selected"}), 400

    panchayat_id = p_row["id"]

    # ⭐ GENERATE NEW TOKEN
    last = conn.execute("SELECT MAX(token_number) FROM tokens").fetchone()[0]
    token_no = 1 if last is None else last + 1

    # ⭐ COUNTERS FOR THAT PANCHAYAT ONLY
    active = conn.execute(
        "SELECT id FROM counters WHERE is_active=1 AND panchayat_id=?",
        (panchayat_id,)
    ).fetchall()

    if not active:
        return jsonify({"error": "No counters active"}), 400

    counter_no = random.choice(active)[0]

    # ⭐ INSERT NEW TOKEN
    conn.execute("""
        INSERT INTO tokens(name, district, panchayat, ward, purpose, token_number,
            counter_number, status, panchayat_id)
        VALUES(?,?,?,?,?,?,?,?,?)
    """, (
        data["name"], data["district"], data["panchayat"], data["ward"],
        data["purpose"], token_no, counter_no, "waiting", panchayat_id
    ))

    conn.commit()
    conn.close()

    session["user_token"] = token_no
    session["user_counter"] = counter_no

    return jsonify({
        "duplicate": False,
        "token": token_no,
        "counter": counter_no
    })

# ---------------- ADMIN LOGIN ----------------
@app.route("/admin/login", methods=["GET","POST"])
def admin_login():
    if request.method == "POST":
        user = request.form["username"]
        pwd = request.form["password"]
        conn = get_db()
        admin = conn.execute("""
            SELECT * FROM panchayat_admins
            WHERE username=? AND password=?
        """, (user, pwd)).fetchone()
        conn.close()

        if admin:
            session["admin"] = True
            session["panchayat_id"] = admin["panchayat_id"]
            return redirect("/admin/dashboard")
        return "Invalid login"

    return render_template("admin_login.html")


@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.clear()
    return redirect("/admin/login")


# ---------------- ADMIN DASHBOARD ----------------
@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin"):
        return redirect("/admin/login")

    p_id = session["panchayat_id"]
    conn = get_db()

    pname = conn.execute("SELECT panchayat_name FROM panchayats WHERE id=?", (p_id,)).fetchone()[0]
    tokens = conn.execute("SELECT * FROM tokens WHERE panchayat_id=?", (p_id,)).fetchall()
    counters = conn.execute("SELECT * FROM counters").fetchall()

    conn.close()
    return render_template("admin.html", tokens=tokens, counters=counters, panchayat_name=pname)


@app.route("/admin/table_reload")
def table_reload():
    if not session.get("admin"):
        return ""

    p_id = session["panchayat_id"]
    conn = get_db()
    rows = conn.execute("SELECT * FROM tokens WHERE panchayat_id=?", (p_id,)).fetchall()
    conn.close()

    return render_template("admin_table.html", tokens=rows)


@app.route("/admin/counters_reload")
def counters_reload():
    conn = get_db()
    counters = conn.execute("SELECT * FROM counters").fetchall()
    conn.close()
    return render_template("admin_counters.html", counters=counters)


# ---------------- ACTIVATE / DEACTIVATE COUNTERS ----------------

@app.route("/activate_counter/<int:id>")
def activate_counter(id):
    p_id = session["panchayat_id"]
    conn = get_db()
    conn.execute("UPDATE counters SET is_active=1, panchayat_id=? WHERE id=?", (p_id, id))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})


@app.route("/deactivate_counter/<int:id>")
def deactivate_counter(id):
    conn = get_db()
    conn.execute("UPDATE counters SET is_active=0, panchayat_id=NULL WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})
    
# ---------------- GET DROPDOWNS ----------------
@app.route("/get_panchayats/<int:district_id>")
def get_panchayats(district_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, panchayat_name FROM panchayats WHERE district_id=?", (district_id,))
    rows = cur.fetchall()
    conn.close()
    return jsonify([{"id": r["id"], "name": r["panchayat_name"]} for r in rows])


@app.route("/get_wards/<panchayat_name>")
def get_wards(panchayat_name):
    conn = get_db()
    cur = conn.cursor()

    panchayat = cur.execute(
        "SELECT id FROM panchayats WHERE TRIM(LOWER(panchayat_name)) = TRIM(LOWER(?))",
        (panchayat_name,)
    ).fetchone()

    if not panchayat:
        conn.close()
        return jsonify([])

    rows = cur.execute(
        "SELECT ward_name FROM wards WHERE panchayat_id=?",
        (panchayat["id"],)
    ).fetchall()

    conn.close()
    return jsonify([{"name": r["ward_name"]} for r in rows])


# ---------------- SERVE / DONE / CANCEL ----------------
@app.route("/serve/<int:id>")
def serve_token(id):
    conn = get_db()
    conn.execute("UPDATE tokens SET status='serving' WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})


@app.route("/done/<int:id>")
def done_token(id):
    conn = get_db()
    conn.execute("UPDATE tokens SET status='done' WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})


@app.route("/cancel/<int:id>")
def cancel_token(id):
    conn = get_db()
    conn.execute("DELETE FROM tokens WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})


# ---------------- COUNTER LIVE DISPLAY ----------------
@app.route("/display/<int:counter_no>")
def display_counter(counter_no):
    conn = get_db()
    tokens = conn.execute("""
        SELECT id, token_number, name, district, panchayat, ward, purpose, status
        FROM tokens
        WHERE counter_number=? AND status!='done'
    """, (counter_no,)).fetchall()
    conn.close()
    return render_template("display.html", tokens=tokens, counter_no=counter_no)


@app.route("/display_table_reload/<int:counter_no>")
def display_table_reload(counter_no):
    conn = get_db()
    rows = conn.execute("""
        SELECT id, token_number, name, district, panchayat, ward, purpose, status
        FROM tokens
        WHERE counter_number=? AND status!='done'
    """, (counter_no,)).fetchall()
    conn.close()

    return render_template("display_rows.html", tokens=rows)


@app.route("/live_data")
def live_data():
    conn = get_db()
    waiting = conn.execute(
        "SELECT COUNT(*) FROM tokens WHERE status='waiting'"
    ).fetchone()[0]
    conn.close()

    return jsonify({"waiting_count": waiting})


@app.route("/live_data/<int:counter_no>")
def live_data_counter(counter_no):
    conn = get_db()
    row = conn.execute("""
        SELECT token_number 
        FROM tokens
        WHERE counter_number=? AND status='serving'
        ORDER BY id DESC LIMIT 1
    """, (counter_no,)).fetchone()
    conn.close()

    return jsonify({"token": row["token_number"] if row else None})


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)