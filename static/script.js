/* ================= CAPTCHA (WELCOME PAGE) ================= */

function refreshCaptcha() {
    let chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
    let captcha = "";

    for (let i = 0; i < 5; i++) {
        captcha += chars[Math.floor(Math.random() * chars.length)];
    }

    document.getElementById("captcha").innerText = captcha;
}

window.onload = refreshCaptcha;

function validateCaptcha() {

    let entered = document.getElementById("captchaInput").value;
    let actual = document.getElementById("captcha").innerText;
    let phone = document.getElementById("phone").value;

    if (!phone) {
        alert("Enter phone number!");
        return;
    }

    if (entered !== actual) {
        alert("Captcha Incorrect!");
        refreshCaptcha();
        return;
    }

    // Send OTP to backend
    fetch("/send_otp", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({phone: phone})
    })
    .then(res => res.json())
    .then(result => {

    alert("Demo OTP: " + result.otp);   // show OTP on screen

    document.getElementById("otp").style.display = "block";
    document.getElementById("verifyBtn").style.display = "block";
});

}

function verifyOTP() {

    let otp = document.getElementById("otp").value;

    if (!otp) {
        alert("Enter OTP!");
        return;
    }

    fetch("/verify_login_otp", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({otp: otp})
    })
    .then(res => res.json())
    .then(result => {

        if (result.status === "success") {
            window.location.href = "/user";
        } else {
            alert("Invalid OTP!");
        }

    });
}


