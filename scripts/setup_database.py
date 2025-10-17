#!/usr/bin/env python3
"""
Database setup script for Global Liquidity Dashboard.
Creates database tables and sets up initial configuration.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.connection import create_tables, check_db_connection, engine
from app.database.models import Base
from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger("setup_database")


def setup_database():
    """Set up the database schema."""
    try:
        logger.info("Starting database setup")
        logger.info(f"Database URL: {str(settings.DATABASE_URL).replace(settings.POSTGRES_PASSWORD, '***')}")

        # Check database connection
        if not check_db_connection():
            logger.error("Cannot connect to database. Please check your configuration.")
            return False

        # Create all tables
        logger.info("Creating database tables...")
        create_tables()

        # Verify tables were created
        with engine.connect() as conn:
            # Check if tables exist
            result = conn.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
            tables = [row[0] for row in result]

        logger.info(f"Created {len(tables)} tables: {', '.join(tables)}")

        # Insert initial configuration data if needed
        setup_initial_data()

        logger.info("Database setup completed successfully!")
        return True

    except Exception as e:
        logger.error(f"Database setup failed: {str(e)}")
        return False


def setup_initial_data():
    """Insert initial configuration data."""
    try:
        logger.info("Setting up initial data...")

        # TODO: Add any initial data setup here
        # For example:
        # - Default asset lists
        # - Configuration parameters
        # - User preferences

        logger.info("Initial data setup completed")

    except Exception as e:
        logger.error(f"Failed to setup initial data: {str(e)}")
        raise


def check_requirements():
    """Check if all requirements are met for database setup."""
    requirements_met = True

    # Check if PostgreSQL is accessible
    if not check_db_connection():
        logger.error("❌ PostgreSQL database is not accessible")
        requirements_met = False
    else:
        logger.info("✅ PostgreSQL database is accessible")

    # Check if required environment variables are set
    required_vars = ["DATABASE_URL"]
    for var in required_vars:
        if not getattr(settings, var.replace("DATABASE_URL", "DATABASE_URL"), None):
            logger.error(f"❌ Environment variable {var} is not set")
            requirements_met = False
        else:
            logger.info(f"✅ Environment variable {var} is set")

    return requirements_met


def main():
    """Main function."""
    print("🌍 Global Liquidity Dashboard - Database Setup")
    print("=" * 50)

    # Check requirements
    if not check_requirements():
        print("\n❌ Requirements not met. Please check your configuration.")
        sys.exit(1)

    # Setup database
    if setup_database():
        print("\n✅ Database setup completed successfully!")
        print("\nNext steps:")
        print("1. Run the data backfill script: python scripts/backfill_data.py")
        print("2. Start the FastAPI server: uvicorn app.main:app --reload")
        print("3. Start the Streamlit dashboard: streamlit run dashboard/app.py")
    else:
        print("\n❌ Database setup failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()