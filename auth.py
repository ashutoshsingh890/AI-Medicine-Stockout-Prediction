import json
import os
import bcrypt

USERS_FILE = "users.json"


def load_users():
    if not os.path.exists(USERS_FILE):
        return {}

    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4)


def register_user(username, password, role):
    users = load_users()

    username = username.strip().lower()

    if not username or not password:
        return False, "Username and password are required."

    if username in users:
        return False, "Username already exists."

    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    users[username] = {
        "password": password_hash,
        "role": role
    }

    save_users(users)

    return True, "Registration successful."


def login_user(username, password):
    users = load_users()

    username = username.strip().lower()

    if username not in users:
        return False, None

    stored_hash = users[username]["password"]

    try:
        valid_password = bcrypt.checkpw(
            password.encode("utf-8"),
            stored_hash.encode("utf-8")
        )
    except Exception:
        return False, None

    if valid_password:
        return True, users[username]["role"]

    return False, None