import os
import psycopg2
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database():
    """Adds missing columns to the chat_sessions table."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable not set.")
        return

    conn = None
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        # --- Add 'channel' column if it doesn't exist ---
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'chat_sessions' AND column_name = 'channel';
        """)
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE chat_sessions
                ADD COLUMN channel VARCHAR(50) NOT NULL DEFAULT 'chat';
            """)
            conn.commit()
            logger.info("Successfully added 'channel' column to 'chat_sessions' table.")
        else:
            logger.info("Column 'channel' already exists in 'chat_sessions' table.")


        # --- Add 'status' column if it doesn't exist ---
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'chat_sessions' AND column_name = 'status';
        """)
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE chat_sessions
                ADD COLUMN status VARCHAR(50) NOT NULL DEFAULT 'active';
            """)
            conn.commit()
            logger.info("Successfully added 'status' column to 'chat_sessions' table.")
        else:
            logger.info("Column 'status' already exists in 'chat_sessions' table.")

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error migrating database: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate_database()
