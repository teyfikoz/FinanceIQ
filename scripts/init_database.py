#!/usr/bin/env python3
"""
Database initialization script for Global Liquidity Dashboard
Creates database schema and optionally seeds demo data
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.database import DatabaseManager, get_db
from utils.authentication import AuthenticationManager
import argparse

def init_database(db_path: str = "data/dashboard.db", demo_data: bool = False):
    """Initialize database with schema"""
    print("🔧 Initializing Global Liquidity Dashboard Database...")
    print(f"📁 Database path: {db_path}")

    # Create database manager
    db = DatabaseManager(db_path)
    print("✅ Database schema created successfully!")

    # Show created tables
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    print(f"\n📊 Created {len(tables)} tables:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"  - {table[0]}: {count} rows")

    if demo_data:
        print("\n🎭 Creating demo data...")
        create_demo_data(db)

    db.close()
    print("\n✅ Database initialization complete!")

def create_demo_data(db: DatabaseManager):
    """Create demo user and sample data"""
    auth = AuthenticationManager(db.db_path)

    # Create demo user
    print("  👤 Creating demo user...")
    if auth.create_user("demo", "demo@example.com", "demo123"):
        print("     ✅ Demo user created (username: demo, password: demo123)")
    else:
        print("     ⚠️  Demo user already exists")

    # Get user ID
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = 'demo'")
    user_row = cursor.fetchone()

    if user_row:
        user_id = user_row[0]

        # Create demo portfolio
        print("  💼 Creating demo portfolio...")
        portfolio_id = db.create_portfolio(
            user_id,
            "Tech Stocks Portfolio",
            "My technology stocks portfolio"
        )

        # Add demo holdings
        print("  📈 Adding demo holdings...")
        demo_holdings = [
            ("AAPL", 10, 150.0, "2024-01-01", "Apple Inc."),
            ("MSFT", 5, 380.0, "2024-01-01", "Microsoft"),
            ("GOOGL", 3, 140.0, "2024-02-01", "Alphabet"),
            ("NVDA", 2, 450.0, "2024-03-01", "NVIDIA"),
        ]

        for symbol, qty, price, date, notes in demo_holdings:
            db.add_holding(portfolio_id, symbol, qty, price, date, notes)
            print(f"     ✅ Added: {symbol} x{qty} @ ${price}")

        # Create demo watchlist
        print("  👁️  Creating demo watchlist...")
        watchlist_id = db.create_watchlist(
            user_id,
            "My Watchlist",
            ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "XU100.IS"]
        )
        print(f"     ✅ Watchlist created with 6 symbols")

        # Create demo alerts
        print("  🔔 Creating demo alerts...")
        demo_alerts = [
            ("AAPL", "price", 160.0, "above"),
            ("TSLA", "price", 200.0, "below"),
        ]

        for symbol, alert_type, threshold, condition in demo_alerts:
            db.create_alert(user_id, symbol, alert_type, threshold, condition)
            print(f"     ✅ Alert: {symbol} {condition} ${threshold}")

def check_database(db_path: str = "data/dashboard.db"):
    """Check database status"""
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False

    print(f"✅ Database exists: {db_path}")

    db = DatabaseManager(db_path)
    conn = db.get_connection()
    cursor = conn.cursor()

    # Count tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"📊 Tables: {len(tables)}")

    # Count users
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    print(f"👤 Users: {user_count}")

    # Count portfolios
    cursor.execute("SELECT COUNT(*) FROM portfolios")
    portfolio_count = cursor.fetchone()[0]
    print(f"💼 Portfolios: {portfolio_count}")

    # Count holdings
    cursor.execute("SELECT COUNT(*) FROM holdings")
    holding_count = cursor.fetchone()[0]
    print(f"📈 Holdings: {holding_count}")

    db.close()
    return True

def reset_database(db_path: str = "data/dashboard.db"):
    """Reset database (delete and recreate)"""
    print(f"⚠️  WARNING: This will delete all data in {db_path}")
    confirm = input("Type 'yes' to continue: ")

    if confirm.lower() != 'yes':
        print("❌ Reset cancelled")
        return

    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"🗑️  Deleted: {db_path}")

    init_database(db_path, demo_data=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Database management for Global Liquidity Dashboard"
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize database schema"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Create demo data (with --init)"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check database status"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset database (delete and recreate)"
    )
    parser.add_argument(
        "--db-path",
        default="data/dashboard.db",
        help="Database file path (default: data/dashboard.db)"
    )

    args = parser.parse_args()

    if args.reset:
        reset_database(args.db_path)
    elif args.init:
        init_database(args.db_path, demo_data=args.demo)
    elif args.check:
        check_database(args.db_path)
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python scripts/init_database.py --init              # Initialize schema")
        print("  python scripts/init_database.py --init --demo       # Initialize with demo data")
        print("  python scripts/init_database.py --check             # Check database status")
        print("  python scripts/init_database.py --reset             # Reset database")
