"""
Authentication system for Global Liquidity Dashboard
Simple session-based authentication with password hashing
"""

import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict
import streamlit as st

class AuthenticationManager:
    """Manages user authentication and sessions"""

    def __init__(self, db_path: str = "data/dashboard.db"):
        """Initialize authentication manager"""
        self.db_path = db_path
        self.session_duration = timedelta(days=7)

    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def generate_session_token(self) -> str:
        """Generate secure session token"""
        return secrets.token_urlsafe(32)

    def create_user(self, username: str, email: str, password: str) -> bool:
        """Create a new user account"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            password_hash = self.hash_password(password)
            cursor.execute(
                """INSERT INTO users (username, email, password_hash)
                   VALUES (?, ?, ?)""",
                (username, email, password_hash)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user and return user data"""
        conn = self.get_connection()
        cursor = conn.cursor()

        password_hash = self.hash_password(password)
        cursor.execute(
            """SELECT id, username, email FROM users
               WHERE username = ? AND password_hash = ?""",
            (username, password_hash)
        )

        user = cursor.fetchone()
        conn.close()

        if user:
            return dict(user)
        return None

    def create_session(self, user_id: int) -> str:
        """Create a new session for user"""
        conn = self.get_connection()
        cursor = conn.cursor()

        session_token = self.generate_session_token()
        expires_at = datetime.now() + self.session_duration

        cursor.execute(
            """INSERT INTO sessions (user_id, session_token, expires_at)
               VALUES (?, ?, ?)""",
            (user_id, session_token, expires_at)
        )

        # Update last login
        cursor.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
            (user_id,)
        )

        conn.commit()
        conn.close()

        return session_token

    def validate_session(self, session_token: str) -> Optional[Dict]:
        """Validate session and return user data"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """SELECT u.id, u.username, u.email, u.preferences
               FROM sessions s
               JOIN users u ON s.user_id = u.id
               WHERE s.session_token = ? AND s.expires_at > CURRENT_TIMESTAMP""",
            (session_token,)
        )

        user = cursor.fetchone()
        conn.close()

        if user:
            return dict(user)
        return None

    def logout(self, session_token: str):
        """Invalidate session"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM sessions WHERE session_token = ?",
            (session_token,)
        )
        conn.commit()
        conn.close()

    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM sessions WHERE expires_at < CURRENT_TIMESTAMP"
        )
        conn.commit()
        conn.close()


def init_session_state():
    """Initialize Streamlit session state for authentication"""
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'session_token' not in st.session_state:
        st.session_state.session_token = None


def show_login_page():
    """Display login/signup page"""
    st.title("🔐 Global Liquidity Dashboard")
    st.markdown("### Professional Financial Analytics Platform")

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    auth = AuthenticationManager()

    with tab1:
        st.subheader("Login to Your Account")
        login_username = st.text_input("Username", key="login_username")
        login_password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login", type="primary"):
            if login_username and login_password:
                user = auth.authenticate_user(login_username, login_password)
                if user:
                    session_token = auth.create_session(user['id'])
                    st.session_state.user = user
                    st.session_state.session_token = session_token
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            else:
                st.warning("Please enter both username and password")

    with tab2:
        st.subheader("Create New Account")
        signup_username = st.text_input("Choose Username", key="signup_username")
        signup_email = st.text_input("Email Address", key="signup_email")
        signup_password = st.text_input("Choose Password", type="password", key="signup_password")
        signup_password_confirm = st.text_input("Confirm Password", type="password", key="signup_password_confirm")

        if st.button("Sign Up", type="primary"):
            if not all([signup_username, signup_email, signup_password, signup_password_confirm]):
                st.warning("Please fill in all fields")
            elif signup_password != signup_password_confirm:
                st.error("Passwords do not match")
            elif len(signup_password) < 6:
                st.error("Password must be at least 6 characters")
            else:
                if auth.create_user(signup_username, signup_email, signup_password):
                    st.success("Account created successfully! Please login.")
                else:
                    st.error("Username or email already exists")


def require_authentication():
    """Require authentication to access the dashboard"""
    init_session_state()

    # Check if user is already logged in
    if st.session_state.session_token:
        auth = AuthenticationManager()
        user = auth.validate_session(st.session_state.session_token)
        if user:
            st.session_state.user = user
            return True
        else:
            # Session expired
            st.session_state.user = None
            st.session_state.session_token = None

    # Show login page
    show_login_page()
    return False


def get_current_user() -> Optional[Dict]:
    """Get current authenticated user"""
    return st.session_state.get('user')


def logout_user():
    """Logout current user"""
    if st.session_state.session_token:
        auth = AuthenticationManager()
        auth.logout(st.session_state.session_token)

    st.session_state.user = None
    st.session_state.session_token = None
    st.rerun()
