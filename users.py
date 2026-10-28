"""User accounts: validation, password hashing and login helpers.

The users collection itself is created in database.py; this file only holds
the logic that works on it.
"""

import re
import uuid
from datetime import datetime

import bcrypt
from pymongo.errors import DuplicateKeyError

import user_database as udb

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_BYTES = 72  # bcrypt only uses the first 72 bytes of a password
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{3,30}$")


# Passwords

def hash_password(password):
    """Hash a plain-text password with bcrypt (the salt is embedded in the hash)."""
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.")
    encoded = password.encode("utf-8")
    if len(encoded) > MAX_PASSWORD_BYTES:
        raise ValueError(f"Password must be at most {MAX_PASSWORD_BYTES} bytes long.")
    return bcrypt.hashpw(encoded, bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password, password_hash):
    """Check a plain-text password against a stored bcrypt hash."""
    try:
        encoded = password.encode("utf-8")
        if len(encoded) > MAX_PASSWORD_BYTES:
            return False
        return bcrypt.checkpw(encoded, password_hash.encode("utf-8"))
    except (ValueError, AttributeError):
        return False


# Fake hash used when the email doesn't exist, so a failed login takes the same
# time either way (prevents discovering which emails are registered).
_DUMMY_HASH = hash_password("dummy-password")


# Users

def _public_user(user):
    """Return the user document without the password hash."""
    if user is None:
        return None
    return {key: value for key, value in user.items() if key != "password_hash"}


def create_user(username, email, password):
    """Register a new user and return it (without the password hash).

    Raises ValueError if the data is invalid or the username/email is taken.
    """
    username = (username or "").strip()
    email = (email or "").strip().lower()

    if not USERNAME_PATTERN.match(username):
        raise ValueError("Username must be 3-30 characters: letters, numbers, '_', '.' or '-'.")
    if not EMAIL_PATTERN.match(email):
        raise ValueError("Please enter a valid email address.")

    user = {
        "_id": uuid.uuid4().hex,
        "username": username,
        "email": email,
        "password_hash": hash_password(password),
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    try:
        udb.get_users_collection().insert_one(user)
    except DuplicateKeyError:
        raise ValueError("That username or email is already registered.") from None
    return _public_user(user)


def authenticate_user(email, password):
    """Return the user (without the hash) if the credentials are valid, else None."""
    email = (email or "").strip().lower()
    user = udb.get_users_collection().find_one({"email": email})
    if user is None:
        verify_password(password or "", _DUMMY_HASH)
        return None
    if not verify_password(password or "", user["password_hash"]):
        return None
    return _public_user(user)


def get_user(user_id):
    """Return a user by id (without the password hash), or None."""
    if not user_id:
        return None
    return _public_user(udb.get_users_collection().find_one({"_id": user_id}))


def change_password(user_id, old_password, new_password):
    """Change a user's password after checking the old one. Returns True on success."""
    users = udb.get_users_collection()
    user = users.find_one({"_id": user_id})
    if user is None or not verify_password(old_password or "", user["password_hash"]):
        return False
    users.update_one(
        {"_id": user_id},
        {"$set": {"password_hash": hash_password(new_password)}},
    )
    return True