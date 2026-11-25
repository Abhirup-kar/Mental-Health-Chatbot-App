/* Authentication form enhancements: password visibility toggle & client validation */

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".toggle-password").forEach((button) => {
    button.addEventListener("click", () => {
      const targetId = button.getAttribute("data-target");
      const input = targetId ? document.getElementById(targetId) : null;
      if (!input) return;

      const showing = input.type === "text";
      input.type = showing ? "password" : "text";
      button.textContent = showing ? "Show" : "Hide";
    });
  });

  const registerForm = document.getElementById("registerForm");
  const errorBox = document.getElementById("authClientError");

  if (registerForm && errorBox) {
    registerForm.addEventListener("submit", (event) => {
      const fullName = document.getElementById("full_name")?.value.trim() || "";
      const username = document.getElementById("username")?.value.trim() || "";
      const email = document.getElementById("email")?.value.trim() || "";
      const password = document.getElementById("password")?.value || "";
      const confirm = document.getElementById("confirm_password")?.value || "";

      let errorMessage = "";
      if (fullName.length < 2) {
        errorMessage = "Please enter your full name (at least 2 characters).";
      } else if (!/^[a-zA-Z0-9_]{3,30}$/.test(username)) {
        errorMessage = "Username must be 3–30 characters using letters, numbers, or underscores.";
      } else if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
        errorMessage = "Please enter a valid email address.";
      } else if (password.length < 6) {
        errorMessage = "Password must be at least 6 characters long.";
      } else if (password !== confirm) {
        errorMessage = "Passwords do not match.";
      }

      if (errorMessage) {
        event.preventDefault();
        errorBox.textContent = errorMessage;
        errorBox.hidden = false;
      } else {
        errorBox.hidden = true;
      }
    });
  }
});
