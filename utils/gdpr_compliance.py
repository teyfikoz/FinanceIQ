"""
GDPR and KVKK Compliance Module for FinanceIQ
Handles user consent, data privacy, and regulatory compliance
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import hashlib


class GDPRComplianceManager:
    """Manages GDPR/KVKK compliance for user data"""

    def __init__(self, db_path: str = "data/dashboard.db"):
        """Initialize GDPR compliance manager"""
        self.db_path = db_path
        self.init_compliance_tables()

    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def init_compliance_tables(self):
        """Initialize GDPR compliance tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # User consent tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_consent (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                consent_type TEXT NOT NULL,
                consent_version TEXT NOT NULL,
                is_granted BOOLEAN NOT NULL,
                granted_at TIMESTAMP,
                withdrawn_at TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Consent versions (Privacy Policy, Terms of Service, etc.)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS consent_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                consent_type TEXT NOT NULL,
                version TEXT NOT NULL,
                content TEXT NOT NULL,
                effective_date TIMESTAMP NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(consent_type, version)
            )
        """)

        # Data processing activities log (Article 30 GDPR)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processing_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                activity_type TEXT NOT NULL,
                purpose TEXT NOT NULL,
                legal_basis TEXT NOT NULL,
                data_categories TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Data access log (audit trail)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_access_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                accessed_by INTEGER,
                access_type TEXT NOT NULL,
                data_type TEXT NOT NULL,
                purpose TEXT,
                ip_address TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (accessed_by) REFERENCES users(id)
            )
        """)

        # Data deletion requests (Right to be forgotten)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deletion_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                scheduled_deletion_date TIMESTAMP,
                status TEXT DEFAULT 'pending',
                completed_at TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Data export requests (Right to data portability)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS export_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                export_format TEXT DEFAULT 'json',
                status TEXT DEFAULT 'pending',
                download_token TEXT,
                completed_at TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Add privacy-related columns to users table if not exists
        try:
            cursor.execute("""
                ALTER TABLE users ADD COLUMN data_retention_days INTEGER DEFAULT 730
            """)
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            cursor.execute("""
                ALTER TABLE users ADD COLUMN anonymize_after_days INTEGER DEFAULT 90
            """)
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("""
                ALTER TABLE users ADD COLUMN last_consent_update TIMESTAMP
            """)
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("""
                ALTER TABLE users ADD COLUMN is_anonymized BOOLEAN DEFAULT 0
            """)
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("""
                ALTER TABLE users ADD COLUMN marketing_consent BOOLEAN DEFAULT 0
            """)
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute("""
                ALTER TABLE users ADD COLUMN analytics_consent BOOLEAN DEFAULT 0
            """)
        except sqlite3.OperationalError:
            pass

        conn.commit()
        conn.close()

    # Consent Management
    def record_consent(self, user_id: int, consent_type: str, version: str,
                      is_granted: bool, ip_address: str = None, user_agent: str = None) -> int:
        """Record user consent for GDPR compliance

        Args:
            user_id: User ID
            consent_type: Type of consent ('privacy_policy', 'terms_of_service', 'marketing', 'analytics')
            version: Version of the consent document
            is_granted: Whether consent is granted
            ip_address: User's IP address
            user_agent: User's browser user agent

        Returns:
            Consent record ID
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        timestamp = datetime.now() if is_granted else None

        cursor.execute("""
            INSERT INTO user_consent
            (user_id, consent_type, consent_version, is_granted, granted_at, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, consent_type, version, is_granted, timestamp, ip_address, user_agent))

        # Update user table
        if consent_type == 'marketing':
            cursor.execute("UPDATE users SET marketing_consent = ?, last_consent_update = CURRENT_TIMESTAMP WHERE id = ?",
                         (is_granted, user_id))
        elif consent_type == 'analytics':
            cursor.execute("UPDATE users SET analytics_consent = ?, last_consent_update = CURRENT_TIMESTAMP WHERE id = ?",
                         (is_granted, user_id))

        conn.commit()
        consent_id = cursor.lastrowid
        conn.close()

        # Log the consent activity
        self.log_processing_activity(
            user_id,
            "consent_update",
            f"User {'granted' if is_granted else 'withdrew'} {consent_type} consent",
            "consent" if is_granted else "consent_withdrawal"
        )

        return consent_id

    def withdraw_consent(self, user_id: int, consent_type: str) -> bool:
        """Withdraw user consent

        Args:
            user_id: User ID
            consent_type: Type of consent to withdraw

        Returns:
            True if successful
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # Get latest consent version
        cursor.execute("""
            SELECT consent_version FROM user_consent
            WHERE user_id = ? AND consent_type = ?
            ORDER BY id DESC LIMIT 1
        """, (user_id, consent_type))

        row = cursor.fetchone()
        if row:
            version = row['consent_version']
            cursor.execute("""
                UPDATE user_consent
                SET is_granted = 0, withdrawn_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND consent_type = ? AND is_granted = 1
            """, (user_id, consent_type))

            # Update user table
            if consent_type == 'marketing':
                cursor.execute("UPDATE users SET marketing_consent = 0 WHERE id = ?", (user_id,))
            elif consent_type == 'analytics':
                cursor.execute("UPDATE users SET analytics_consent = 0 WHERE id = ?", (user_id,))

            conn.commit()
            conn.close()

            self.log_processing_activity(
                user_id,
                "consent_withdrawal",
                f"User withdrew {consent_type} consent",
                "consent_withdrawal"
            )
            return True

        conn.close()
        return False

    def get_user_consents(self, user_id: int) -> Dict[str, bool]:
        """Get all current consents for a user

        Args:
            user_id: User ID

        Returns:
            Dictionary of consent types and their status
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT consent_type, is_granted
            FROM user_consent
            WHERE user_id = ? AND id IN (
                SELECT MAX(id) FROM user_consent WHERE user_id = ? GROUP BY consent_type
            )
        """, (user_id, user_id))

        consents = {row['consent_type']: bool(row['is_granted']) for row in cursor.fetchall()}
        conn.close()

        return consents

    def check_consent(self, user_id: int, consent_type: str) -> bool:
        """Check if user has granted specific consent

        Args:
            user_id: User ID
            consent_type: Type of consent

        Returns:
            True if consent is granted
        """
        consents = self.get_user_consents(user_id)
        return consents.get(consent_type, False)

    # Consent Version Management
    def add_consent_version(self, consent_type: str, version: str, content: str,
                           effective_date: datetime = None) -> int:
        """Add new version of consent document

        Args:
            consent_type: Type of consent
            version: Version string (e.g., "1.0", "2023.1")
            content: Full text of the consent document
            effective_date: When this version becomes effective

        Returns:
            Version ID
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        if effective_date is None:
            effective_date = datetime.now()

        # Deactivate previous versions
        cursor.execute("""
            UPDATE consent_versions
            SET is_active = 0
            WHERE consent_type = ?
        """, (consent_type,))

        cursor.execute("""
            INSERT INTO consent_versions
            (consent_type, version, content, effective_date, is_active)
            VALUES (?, ?, ?, ?, 1)
        """, (consent_type, version, content, effective_date))

        conn.commit()
        version_id = cursor.lastrowid
        conn.close()

        return version_id

    def get_active_consent_version(self, consent_type: str) -> Optional[Dict]:
        """Get active version of consent document

        Args:
            consent_type: Type of consent

        Returns:
            Consent version data or None
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM consent_versions
            WHERE consent_type = ? AND is_active = 1
            ORDER BY effective_date DESC
            LIMIT 1
        """, (consent_type,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    # Data Processing Activity Logging (GDPR Article 30)
    def log_processing_activity(self, user_id: int, activity_type: str,
                                purpose: str, legal_basis: str,
                                data_categories: List[str] = None):
        """Log data processing activity for GDPR compliance

        Args:
            user_id: User ID
            activity_type: Type of processing activity
            purpose: Purpose of processing
            legal_basis: Legal basis for processing (consent, contract, legitimate_interest, etc.)
            data_categories: Categories of data processed
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        if data_categories is None:
            data_categories = []

        cursor.execute("""
            INSERT INTO processing_activities
            (user_id, activity_type, purpose, legal_basis, data_categories)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, activity_type, purpose, legal_basis, json.dumps(data_categories)))

        conn.commit()
        conn.close()

    # Data Access Logging
    def log_data_access(self, user_id: int, accessed_by: int, access_type: str,
                       data_type: str, purpose: str = None, ip_address: str = None):
        """Log data access for audit trail

        Args:
            user_id: ID of user whose data was accessed
            accessed_by: ID of user who accessed the data
            access_type: Type of access (read, write, delete, export)
            data_type: Type of data accessed
            purpose: Purpose of access
            ip_address: IP address of accessor
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO data_access_log
            (user_id, accessed_by, access_type, data_type, purpose, ip_address)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, accessed_by, access_type, data_type, purpose, ip_address))

        conn.commit()
        conn.close()

    # Right to be Forgotten
    def request_data_deletion(self, user_id: int, grace_period_days: int = 30) -> int:
        """Request deletion of user data (Right to be forgotten)

        Args:
            user_id: User ID
            grace_period_days: Days before actual deletion (default 30)

        Returns:
            Deletion request ID
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        scheduled_date = datetime.now() + timedelta(days=grace_period_days)

        cursor.execute("""
            INSERT INTO deletion_requests
            (user_id, scheduled_deletion_date, status)
            VALUES (?, ?, 'pending')
        """, (user_id, scheduled_date))

        conn.commit()
        request_id = cursor.lastrowid
        conn.close()

        self.log_processing_activity(
            user_id,
            "deletion_request",
            "User requested data deletion (Right to be forgotten)",
            "user_request"
        )

        return request_id

    def cancel_deletion_request(self, request_id: int) -> bool:
        """Cancel a pending deletion request

        Args:
            request_id: Deletion request ID

        Returns:
            True if cancelled successfully
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE deletion_requests
            SET status = 'cancelled'
            WHERE id = ? AND status = 'pending'
        """, (request_id,))

        success = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return success

    def execute_data_deletion(self, user_id: int) -> bool:
        """Execute data deletion for a user

        Args:
            user_id: User ID

        Returns:
            True if successful
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Delete user data from all tables
            cursor.execute("DELETE FROM holdings WHERE portfolio_id IN (SELECT id FROM portfolios WHERE user_id = ?)", (user_id,))
            cursor.execute("DELETE FROM transactions WHERE portfolio_id IN (SELECT id FROM portfolios WHERE user_id = ?)", (user_id,))
            cursor.execute("DELETE FROM portfolios WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM watchlists WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM alerts WHERE user_id = ?", (user_id,))
            cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))

            # Anonymize user record instead of deleting (for audit trail)
            anon_hash = hashlib.sha256(f"deleted_{user_id}_{datetime.now()}".encode()).hexdigest()[:16]
            cursor.execute("""
                UPDATE users
                SET username = ?,
                    email = ?,
                    password_hash = '',
                    is_anonymized = 1,
                    preferences = NULL
                WHERE id = ?
            """, (f"deleted_user_{anon_hash}", f"deleted_{anon_hash}@anonymized.local", user_id))

            # Update deletion request status
            cursor.execute("""
                UPDATE deletion_requests
                SET status = 'completed', completed_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND status = 'pending'
            """, (user_id,))

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            conn.rollback()
            conn.close()
            return False

    # Right to Data Portability
    def export_user_data(self, user_id: int) -> Dict[str, Any]:
        """Export all user data in machine-readable format (Right to data portability)

        Args:
            user_id: User ID

        Returns:
            Dictionary containing all user data
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        # User information
        cursor.execute("SELECT username, email, created_at, last_login FROM users WHERE id = ?", (user_id,))
        user_data = dict(cursor.fetchone()) if cursor.fetchone() else {}

        # Portfolios
        cursor.execute("SELECT * FROM portfolios WHERE user_id = ?", (user_id,))
        portfolios = [dict(row) for row in cursor.fetchall()]

        # Holdings
        for portfolio in portfolios:
            cursor.execute("SELECT * FROM holdings WHERE portfolio_id = ?", (portfolio['id'],))
            portfolio['holdings'] = [dict(row) for row in cursor.fetchall()]

        # Transactions
        for portfolio in portfolios:
            cursor.execute("SELECT * FROM transactions WHERE portfolio_id = ?", (portfolio['id'],))
            portfolio['transactions'] = [dict(row) for row in cursor.fetchall()]

        # Watchlists
        cursor.execute("SELECT * FROM watchlists WHERE user_id = ?", (user_id,))
        watchlists = [dict(row) for row in cursor.fetchall()]

        # Alerts
        cursor.execute("SELECT * FROM alerts WHERE user_id = ?", (user_id,))
        alerts = [dict(row) for row in cursor.fetchall()]

        # Consents
        cursor.execute("SELECT * FROM user_consent WHERE user_id = ?", (user_id,))
        consents = [dict(row) for row in cursor.fetchall()]

        conn.close()

        # Log the export
        self.log_data_access(user_id, user_id, 'export', 'all_user_data', 'Data portability request')

        return {
            'export_date': datetime.now().isoformat(),
            'user': user_data,
            'portfolios': portfolios,
            'watchlists': watchlists,
            'alerts': alerts,
            'consents': consents
        }

    # Data Retention
    def get_users_for_retention_cleanup(self, inactive_days: int = 730) -> List[int]:
        """Get users who should be cleaned up based on retention policy

        Args:
            inactive_days: Days of inactivity before cleanup

        Returns:
            List of user IDs
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cutoff_date = datetime.now() - timedelta(days=inactive_days)

        cursor.execute("""
            SELECT id FROM users
            WHERE (last_login < ? OR last_login IS NULL)
            AND created_at < ?
            AND is_anonymized = 0
        """, (cutoff_date, cutoff_date))

        user_ids = [row['id'] for row in cursor.fetchall()]
        conn.close()

        return user_ids

    # Audit and Reporting
    def get_consent_audit_trail(self, user_id: int) -> List[Dict]:
        """Get full consent audit trail for a user

        Args:
            user_id: User ID

        Returns:
            List of consent records
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM user_consent
            WHERE user_id = ?
            ORDER BY id DESC
        """, (user_id,))

        records = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return records

    def get_data_access_audit_trail(self, user_id: int, days: int = 90) -> List[Dict]:
        """Get data access audit trail for a user

        Args:
            user_id: User ID
            days: Number of days to look back

        Returns:
            List of access records
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        cutoff_date = datetime.now() - timedelta(days=days)

        cursor.execute("""
            SELECT * FROM data_access_log
            WHERE user_id = ? AND timestamp > ?
            ORDER BY timestamp DESC
        """, (user_id, cutoff_date))

        records = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return records
