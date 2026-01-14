// ================= CAPTCHA & OTP (welcome.html) =================

// Generate / Refresh CAPTCHA
function refreshCaptcha() {
    document.getElementById("captcha").innerText =
        Math.random().toString(36).substring(2, 7).toUpperCase();
}

// Validate CAPTCHA before OTP
function validateCaptcha() {
    let shown = document.getElementById("captcha").innerText;
    let entered = document.getElementById("captchaInput").value;

    if (entered === shown) {
        document.getElementById("otp").style.display = "block";
        document.getElementById("verifyBtn").style.display = "block";
        alert("CAPTCHA verified. OTP generated (demo).");
    } else {
        alert("Invalid CAPTCHA. Try again.");
        refreshCaptcha();
    }
}

// Redirect to user page
function goToUser() {
    window.location.href = "/user";
}


// ================= TOKEN GENERATION (user.html) =================

// Generate token and update LIVE dashboard
function generateToken() {
    let token = Math.floor(Math.random() * 100) + 1;
    let counter = Math.floor(Math.random() * 5) + 1;

    document.getElementById("liveToken").innerText = token;
    document.getElementById("liveCounter").innerText = counter;
}
/* ===== District → Panchayat → Ward Data ===== */

const data = {
    "Ernakulam": {
        "Aluva": [1, 2, 3, 4, 5],
        "Kothamangalam": [1, 2, 3]
    },
    "Kozhikode": {
        "Balussery": [1, 2, 3, 4],
        "Kunnamangalam": [1, 2]
    },
    "Trivandrum": {
        "Neyyattinkara": [1, 2, 3],
        "Varkala": [1, 2, 3, 4]
    }
};

function loadPanchayats() {
    let district = document.getElementById("district").value;
    let panchayat = document.getElementById("panchayat");
    let ward = document.getElementById("ward");

    panchayat.innerHTML = '<option value="">Select Panchayat</option>';
    ward.innerHTML = '<option value="">Select Ward Number</option>';

    if (district && data[district]) {
        for (let p in data[district]) {
            let option = document.createElement("option");
            option.value = p;
            option.text = p;
            panchayat.add(option);
        }
    }
}

function loadWards() {
    let district = document.getElementById("district").value;
    let panchayat = document.getElementById("panchayat").value;
    let ward = document.getElementById("ward");

    ward.innerHTML = '<option value="">Select Ward Number</option>';

    if (district && panchayat && data[district][panchayat]) {
        data[district][panchayat].forEach(w => {
            let option = document.createElement("option");
            option.value = w;
            option.text = "Ward " + w;
            ward.add(option);
        });
    }
}
function sendTokenData() {

    let data = {
        name: document.querySelector("input[placeholder='First Name']").value,
        district: document.getElementById("district").value,
        panchayat: document.getElementById("panchayat").value,
        ward: document.getElementById("ward").value,
        purpose: document.querySelector("select:last-of-type").value
    };

    fetch("/generate_token", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(result => {
        document.getElementById("liveToken").innerText = result.token;
        document.getElementById("liveCounter").innerText = result.counter;
    });
}
/* ===== Kerala District → Panchayat Data (Sample) ===== */

const keralaData = {
    "Thiruvananthapuram": ["Varkala", "Neyyattinkara", "Kattakada"],
    "Kollam": ["Kottarakkara", "Punalur"],
    "Pathanamthitta": ["Adoor", "Konni"],
    "Alappuzha": ["Cherthala", "Ambalappuzha"],
    "Kottayam": ["Pala", "Vaikom"],
    "Idukki": ["Thodupuzha", "Adimali"],
    "Ernakulam": ["Aluva", "Kothamangalam", "Muvattupuzha"],
    "Thrissur": ["Chalakudy", "Irinjalakuda"],
    "Palakkad": ["Ottapalam", "Mannarkkad"],
    "Malappuram": ["Manjeri", "Perinthalmanna"],
    "Kozhikode": ["Balussery", "Kunnamangalam"],
    "Wayanad": ["Kalpetta", "Mananthavady"],
    "Kannur": ["Taliparamba", "Iritty"],
    "Kasaragod": ["Kanhiradukkam", "Manjeshwar"]
};

function loadPanchayats() {
    let district = document.getElementById("district").value;
    let panchayat = document.getElementById("panchayat");
    let ward = document.getElementById("ward");

    panchayat.innerHTML = '<option value="">Select Panchayat</option>';
    ward.innerHTML = '<option value="">Select Ward Number</option>';

    if (keralaData[district]) {
        keralaData[district].forEach(p => {
            let opt = document.createElement("option");
            opt.value = p;
            opt.text = p;
            panchayat.add(opt);
        });
    }
}

function loadWards() {
    let ward = document.getElementById("ward");
    ward.innerHTML = '<option value="">Select Ward Number</option>';

    // Typical ward count (1–20)
    for (let i = 1; i <= 20; i++) {
        let opt = document.createElement("option");
        opt.value = i;
        opt.text = "Ward " + i;
        ward.add(opt);
    }
}

