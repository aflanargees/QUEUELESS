/* ================= CAPTCHA (WELCOME PAGE) ================= */

function refreshCaptcha() {
    let chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
    let cap = "";
    for (let i = 0; i < 5; i++) {
        cap += chars[Math.floor(Math.random() * chars.length)];
    }
    document.getElementById("captcha").innerText = cap;
}

function validateCaptcha() {
    let shown = document.getElementById("captcha").innerText.trim();
    let entered = document.getElementById("captchaInput").value.trim();

    if (entered === shown) {
        document.getElementById("otp").style.display = "block";
        document.getElementById("verifyBtn").style.display = "block";
        alert("CAPTCHA Verified. OTP Generated (Demo Only).");
    } else {
        alert("Incorrect CAPTCHA. Try again.");
        refreshCaptcha();
    }
}

function goToUser() {
    window.location.href = "/user";
}

window.onload = () => {
    if (document.getElementById("captcha")) refreshCaptcha();
};
