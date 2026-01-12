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

