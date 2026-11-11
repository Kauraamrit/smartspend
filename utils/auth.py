import streamlit as st
from passlib.context import CryptContext

from database.db import get_db
from database.models import User


# Password hashing configuration
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password):
    """Convert a plain-text password into a secure hash."""
    return pwd_context.hash(password)


def verify_password(password, password_hash):
    """Check whether a password matches its stored hash."""
    return pwd_context.verify(password, password_hash)


def register_user(name, email, password):
    """Create a new user account."""

    db = get_db()

    try:
        # Check whether email already exists
        existing_user = (
            db.query(User)
            .filter(User.email == email.lower().strip())
            .first()
        )

        if existing_user:
            return False, "An account with this email already exists."

        # Create user
        new_user = User(
            name=name.strip(),
            email=email.lower().strip(),
            password_hash=hash_password(password)
        )

        db.add(new_user)
        db.commit()

        return True, "Account created successfully!"

    except Exception as e:
        db.rollback()
        return False, f"Registration failed: {e}"

    finally:
        db.close()


def login_user(email, password):
    """Authenticate an existing user."""

    db = get_db()

    try:
        user = (
            db.query(User)
            .filter(User.email == email.lower().strip())
            .first()
        )

        if not user:
            return False, "Invalid email or password."

        if not verify_password(password, user.password_hash):
            return False, "Invalid email or password."

        # Store logged-in user in Streamlit session
        st.session_state["logged_in"] = True
        st.session_state["user_id"] = user.id
        st.session_state["user_name"] = user.name
        st.session_state["user_email"] = user.email

        return True, "Login successful!"

    finally:
        db.close()


def logout_user():
    """Log out the current user."""

    keys_to_remove = [
        "logged_in",
        "user_id",
        "user_name",
        "user_email"
    ]

    for key in keys_to_remove:
        st.session_state.pop(key, None)


def is_logged_in():
    """Check whether a user is currently logged in."""

    return st.session_state.get("logged_in", False)