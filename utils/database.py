"""
Database integration for Global Liquidity Dashboard
SQLite-based persistence for user data, portfolios, and historical tracking
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd
from pathlib import Path

class DatabaseManager:
    """Manages database operations for the dashboard"""

    def __init__(self, db_path: str = "data/dashboard.db"):
        """Initialize database connection"""
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self.init_database()

    def get_connection(self):
        """Get database connection"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        return self.conn

    def init_database(self):
        """Initialize database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                preferences TEXT
            )
        """)

        # Portfolios table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Portfolio holdings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                quantity REAL NOT NULL,
                purchase_price REAL NOT NULL,
                purchase_date DATE NOT NULL,
                notes TEXT,
                FOREIGN KEY (portfolio_id) REFERENCES portfolios(id)
            )
        """)

        # Watchlists table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                symbols TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Price history cache
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                date DATE NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, date)
            )
        """)

        # Alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                threshold REAL NOT NULL,
                condition TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                triggered_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Market data cache
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cache_key TEXT UNIQUE NOT NULL,
                data TEXT NOT NULL,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL
            )
        """)

        # User sessions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                date DATE NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (portfolio_id) REFERENCES portfolios(id)
            )
        """)

        conn.commit()

    # Portfolio Management
    def create_portfolio(self, user_id: int, name: str, description: str = "") -> int:
        """Create a new portfolio"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO portfolios (user_id, name, description) VALUES (?, ?, ?)",
            (user_id, name, description)
        )
        conn.commit()
        return cursor.lastrowid

    def add_holding(self, portfolio_id: int, symbol: str, quantity: float,
                    purchase_price: float, purchase_date: str, notes: str = ""):
        """Add a holding to portfolio"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO holdings
               (portfolio_id, symbol, quantity, purchase_price, purchase_date, notes)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (portfolio_id, symbol, quantity, purchase_price, purchase_date, notes)
        )
        conn.commit()

    def get_portfolio_holdings(self, portfolio_id: int) -> List[Dict]:
        """Get all holdings for a portfolio"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM holdings WHERE portfolio_id = ?",
            (portfolio_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_user_portfolios(self, user_id: int) -> List[Dict]:
        """Get all portfolios for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM portfolios WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def update_holding(self, holding_id: int, quantity: float = None,
                      notes: str = None):
        """Update a holding"""
        conn = self.get_connection()
        cursor = conn.cursor()
        updates = []
        params = []

        if quantity is not None:
            updates.append("quantity = ?")
            params.append(quantity)
        if notes is not None:
            updates.append("notes = ?")
            params.append(notes)

        if updates:
            params.append(holding_id)
            cursor.execute(
                f"UPDATE holdings SET {', '.join(updates)} WHERE id = ?",
                params
            )
            conn.commit()

    def delete_holding(self, holding_id: int):
        """Delete a holding"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM holdings WHERE id = ?", (holding_id,))
        conn.commit()

    # Transaction history
    def add_transaction(self, portfolio_id: int, symbol: str, transaction_type: str,
                       quantity: float, price: float, date: str, notes: str = ""):
        """Add a transaction record"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO transactions
               (portfolio_id, symbol, transaction_type, quantity, price, date, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (portfolio_id, symbol, transaction_type, quantity, price, date, notes)
        )
        conn.commit()
        return cursor.lastrowid

    def get_portfolio_transactions(self, portfolio_id: int) -> List[Dict]:
        """Get all transactions for a portfolio"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT * FROM transactions
               WHERE portfolio_id = ?
               ORDER BY date DESC, id DESC""",
            (portfolio_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    # Watchlist Management
    def create_watchlist(self, user_id: int, name: str, symbols: List[str]) -> int:
        """Create a new watchlist"""
        conn = self.get_connection()
        cursor = conn.cursor()
        symbols_json = json.dumps(symbols)
        cursor.execute(
            "INSERT INTO watchlists (user_id, name, symbols) VALUES (?, ?, ?)",
            (user_id, name, symbols_json)
        )
        conn.commit()
        return cursor.lastrowid

    def get_user_watchlists(self, user_id: int) -> List[Dict]:
        """Get all watchlists for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM watchlists WHERE user_id = ?",
            (user_id,)
        )
        watchlists = []
        for row in cursor.fetchall():
            watchlist = dict(row)
            watchlist['symbols'] = json.loads(watchlist['symbols'])
            watchlists.append(watchlist)
        return watchlists

    def update_watchlist(self, watchlist_id: int, symbols: List[str]):
        """Update watchlist symbols"""
        conn = self.get_connection()
        cursor = conn.cursor()
        symbols_json = json.dumps(symbols)
        cursor.execute(
            "UPDATE watchlists SET symbols = ? WHERE id = ?",
            (symbols_json, watchlist_id)
        )
        conn.commit()

    # Alert Management
    def create_alert(self, user_id: int, symbol: str, alert_type: str,
                    threshold: float, condition: str) -> int:
        """Create a price alert"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO alerts
               (user_id, symbol, alert_type, threshold, condition)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, symbol, alert_type, threshold, condition)
        )
        conn.commit()
        return cursor.lastrowid

    def get_active_alerts(self, user_id: int) -> List[Dict]:
        """Get all active alerts for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT * FROM alerts
               WHERE user_id = ? AND is_active = 1
               ORDER BY created_at DESC""",
            (user_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def trigger_alert(self, alert_id: int):
        """Mark alert as triggered"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE alerts
               SET is_active = 0, triggered_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (alert_id,)
        )
        conn.commit()

    # Cache Management
    def cache_price_data(self, symbol: str, df: pd.DataFrame):
        """Cache historical price data"""
        conn = self.get_connection()
        cursor = conn.cursor()

        for idx, row in df.iterrows():
            cursor.execute(
                """INSERT OR REPLACE INTO price_history
                   (symbol, date, open, high, low, close, volume)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (symbol, idx.strftime('%Y-%m-%d'), row.get('Open'),
                 row.get('High'), row.get('Low'), row.get('Close'),
                 row.get('Volume'))
            )
        conn.commit()

    def get_cached_price_data(self, symbol: str, start_date: str,
                             end_date: str) -> Optional[pd.DataFrame]:
        """Get cached price data"""
        conn = self.get_connection()
        query = """
            SELECT date, open, high, low, close, volume
            FROM price_history
            WHERE symbol = ? AND date BETWEEN ? AND ?
            ORDER BY date
        """
        df = pd.read_sql_query(query, conn, params=(symbol, start_date, end_date))

        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            return df
        return None

    def set_cache(self, cache_key: str, data: Any, ttl_seconds: int = 300):
        """Set cache with expiration"""
        conn = self.get_connection()
        cursor = conn.cursor()
        data_json = json.dumps(data)
        expires_at = datetime.now().timestamp() + ttl_seconds

        cursor.execute(
            """INSERT OR REPLACE INTO market_cache
               (cache_key, data, expires_at)
               VALUES (?, ?, datetime(?, 'unixepoch'))""",
            (cache_key, data_json, expires_at)
        )
        conn.commit()

    def get_cache(self, cache_key: str) -> Optional[Any]:
        """Get cached data if not expired"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT data FROM market_cache
               WHERE cache_key = ? AND expires_at > CURRENT_TIMESTAMP""",
            (cache_key,)
        )
        row = cursor.fetchone()
        if row:
            return json.loads(row['data'])
        return None

    def clear_expired_cache(self):
        """Clear expired cache entries"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM market_cache WHERE expires_at < CURRENT_TIMESTAMP"
        )
        cursor.execute(
            "DELETE FROM price_history WHERE cached_at < datetime('now', '-30 days')"
        )
        conn.commit()

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

# Global database instance
_db_instance = None

def get_db() -> DatabaseManager:
    """Get global database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance
