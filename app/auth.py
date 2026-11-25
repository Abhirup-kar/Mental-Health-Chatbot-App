"""Authentication blueprint handling user registration, login, and session state."""

from __future__ import annotations

import functools
import re
from typing import Any, Callable

from flask import (
    Blueprint,
    current_app,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

auth_bp = Blueprint("auth", __name__)

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,30}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def login_required(view: Callable[..., Any]) -> Callable[..., Any]:
    """Require an authenticated user for HTML pages (redirect) or API routes (401 JSON)."""

    @functools.wraps(view)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        if g.user is None:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Authentication required."}), 401
            flash("Please log in to access the Mental Health Chatbot.", "warning")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


@auth_bp.before_app_request
def load_logged_in_user() -> None:
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        db = current_app.extensions["db"]
        user = db.get_user_by_id(int(user_id))
        if user is None:
            session.clear()
        g.user = user


@auth_bp.route("/")
def index() -> Any:
    return render_template("index.html", user=g.user)


@auth_bp.route("/register", methods=["GET", "POST"])
def register() -> Any:
    if g.user is not None:
        return redirect(url_for("chat.chat_page"))

    if request.method == "POST":
        full_name = (request.form.get("full_name") or "").strip()
        username = (request.form.get("username") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        confirm_password = request.form.get("confirm_password") or ""

        error: str | None = None
        if len(full_name) < 2 or len(full_name) > 120:
            error = "Full name must be between 2 and 120 characters."
        elif not _USERNAME_RE.match(username):
            error = "Username must be 3–30 characters using only letters, numbers, and underscores."
        elif not _EMAIL_RE.match(email):
            error = "Please enter a valid email address."
        elif len(password) < 6:
            error = "Password must be at least 6 characters long."
        elif password != confirm_password:
            error = "Passwords do not match."

        db = current_app.extensions["db"]
        if error is None and db.get_user_by_username(username) is not None:
            error = "That username is already taken. Please choose another."
        if error is None and db.get_user_by_email(email) is not None:
            error = "An account with that email address already exists."

        if error is None:
            password_hash = generate_password_hash(password)
            db.create_user(full_name, username, email, password_hash)
            flash("Registration successful! Please log in to start chatting.", "success")
            return redirect(url_for("auth.login"))

        flash(error, "error")
        return render_template(
            "register.html",
            form_data={"full_name": full_name, "username": username, "email": email},
        ), 400

    return render_template("register.html", form_data={})


@auth_bp.route("/login", methods=["GET", "POST"])
def login() -> Any:
    if g.user is not None:
        return redirect(url_for("chat.chat_page"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        db = current_app.extensions["db"]
        user = db.get_user_by_username(username)

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Invalid username or password. Please try again.", "error")
            return render_template("login.html", username=username), 401

        session.clear()
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["full_name"] = user["full_name"]
        flash(f"Welcome back, {user['full_name']}!", "success")
        return redirect(url_for("chat.chat_page"))

    return render_template("login.html", username="")


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout() -> Any:
    session.clear()
    flash("You have been logged out safely.", "info")
    return redirect(url_for("auth.login"))
