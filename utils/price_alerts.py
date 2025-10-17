"""Price alert system for stocks"""
import streamlit as st
import sqlite3
from datetime import datetime
from typing import List, Dict


class PriceAlertManager:
    """Manage price alerts for stocks"""

    def __init__(self, db_path: str = "data/dashboard.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize alerts table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                target_price REAL NOT NULL,
                condition TEXT NOT NULL,
                current_price REAL,
                is_triggered BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                triggered_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        conn.commit()
        conn.close()

    def create_alert(self, user_id: int, symbol: str, target_price: float,
                     condition: str, current_price: float = None) -> bool:
        """Create a new price alert

        Args:
            user_id: User ID
            symbol: Stock symbol
            target_price: Target price for alert
            condition: 'above' or 'below'
            current_price: Current stock price

        Returns:
            True if created successfully
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO price_alerts (user_id, symbol, target_price, condition, current_price)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, symbol.upper(), target_price, condition.lower(), current_price))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"Error creating alert: {str(e)}")
            return False

    def get_user_alerts(self, user_id: int, include_triggered: bool = False) -> List[Dict]:
        """Get all alerts for a user

        Args:
            user_id: User ID
            include_triggered: Include triggered alerts

        Returns:
            List of alerts
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if include_triggered:
                cursor.execute("""
                    SELECT * FROM price_alerts
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                """, (user_id,))
            else:
                cursor.execute("""
                    SELECT * FROM price_alerts
                    WHERE user_id = ? AND is_triggered = 0
                    ORDER BY created_at DESC
                """, (user_id,))

            alerts = [dict(row) for row in cursor.fetchall()]
            conn.close()

            return alerts

        except Exception as e:
            print(f"Error getting alerts: {str(e)}")
            return []

    def check_alerts(self, user_id: int, symbol: str, current_price: float) -> List[Dict]:
        """Check if any alerts are triggered

        Args:
            user_id: User ID
            symbol: Stock symbol
            current_price: Current stock price

        Returns:
            List of triggered alerts
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get active alerts for this symbol
            cursor.execute("""
                SELECT * FROM price_alerts
                WHERE user_id = ? AND symbol = ? AND is_triggered = 0
            """, (user_id, symbol.upper()))

            alerts = cursor.fetchall()
            triggered = []

            for alert in alerts:
                alert_dict = dict(alert)
                condition_met = False

                if alert_dict['condition'] == 'above' and current_price >= alert_dict['target_price']:
                    condition_met = True
                elif alert_dict['condition'] == 'below' and current_price <= alert_dict['target_price']:
                    condition_met = True

                if condition_met:
                    # Mark as triggered
                    cursor.execute("""
                        UPDATE price_alerts
                        SET is_triggered = 1, triggered_at = ?, current_price = ?
                        WHERE id = ?
                    """, (datetime.now(), current_price, alert_dict['id']))

                    alert_dict['is_triggered'] = True
                    alert_dict['triggered_at'] = datetime.now()
                    triggered.append(alert_dict)

            conn.commit()
            conn.close()

            return triggered

        except Exception as e:
            print(f"Error checking alerts: {str(e)}")
            return []

    def delete_alert(self, alert_id: int, user_id: int) -> bool:
        """Delete an alert

        Args:
            alert_id: Alert ID
            user_id: User ID (for security)

        Returns:
            True if deleted successfully
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM price_alerts
                WHERE id = ? AND user_id = ?
            """, (alert_id, user_id))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"Error deleting alert: {str(e)}")
            return False


def create_price_alerts_ui(user_id: int):
    """Create price alerts UI

    Args:
        user_id: Current user ID
    """
    st.header("🔔 Price Alerts")

    alert_manager = PriceAlertManager()

    # Create new alert
    with st.expander("➕ Create New Alert", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            symbol = st.text_input("Stock Symbol", key="alert_symbol").upper()

        with col2:
            target_price = st.number_input("Target Price", min_value=0.01, value=100.0,
                                          step=0.01, key="alert_target")

        with col3:
            condition = st.selectbox("Condition", ["Above", "Below"], key="alert_condition")

        if st.button("Create Alert", type="primary"):
            if symbol:
                # Get current price (you can fetch from yfinance here)
                import yfinance as yf
                try:
                    ticker = yf.Ticker(symbol)
                    current_price = ticker.info.get('currentPrice', ticker.info.get('regularMarketPrice', 0))
                except:
                    current_price = 0

                success = alert_manager.create_alert(
                    user_id=user_id,
                    symbol=symbol,
                    target_price=target_price,
                    condition=condition.lower(),
                    current_price=current_price
                )

                if success:
                    st.success(f"✅ Alert created for {symbol} {condition.lower()} ${target_price:.2f}")
                    st.rerun()
                else:
                    st.error("Failed to create alert")
            else:
                st.warning("Please enter a stock symbol")

    # Display active alerts
    st.subheader("📋 Active Alerts")
    alerts = alert_manager.get_user_alerts(user_id, include_triggered=False)

    if alerts:
        for alert in alerts:
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

            with col1:
                st.markdown(f"**{alert['symbol']}**")

            with col2:
                direction = "↗️" if alert['condition'] == 'above' else "↘️"
                st.markdown(f"{direction} {alert['condition'].title()}")

            with col3:
                st.markdown(f"**${alert['target_price']:.2f}**")

            with col4:
                if st.button("🗑️", key=f"delete_{alert['id']}"):
                    alert_manager.delete_alert(alert['id'], user_id)
                    st.rerun()

        st.markdown("---")
    else:
        st.info("No active alerts. Create one above!")

    # Display triggered alerts
    st.subheader("✅ Triggered Alerts (Last 10)")
    triggered_alerts = alert_manager.get_user_alerts(user_id, include_triggered=True)
    triggered_alerts = [a for a in triggered_alerts if a['is_triggered']][:10]

    if triggered_alerts:
        for alert in triggered_alerts:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown(f"**{alert['symbol']}**")

            with col2:
                st.markdown(f"{alert['condition'].title()} ${alert['target_price']:.2f}")

            with col3:
                st.markdown(f"Triggered at: ${alert['current_price']:.2f}")

            with col4:
                st.markdown(f"🕐 {alert['triggered_at'][:10] if alert['triggered_at'] else 'N/A'}")
    else:
        st.info("No triggered alerts yet")
