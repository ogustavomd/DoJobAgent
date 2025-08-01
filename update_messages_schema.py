import os
import psycopg2
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database():
    """Adds the sender_name column to the messages table."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable not set.")
        return

    conn = None
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        # --- Add 'sender_name' column if it doesn't exist ---
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'messages' AND column_name = 'sender_name';
        """)
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE messages
                ADD COLUMN sender_name TEXT NULL;
            """)
            conn.commit()
            logger.info("Successfully added 'sender_name' column to 'messages' table.")
        else:
            logger.info("Column 'sender_name' already exists in 'messages' table.")

        # --- Add 'is_from_bot' column if it doesn't exist ---
        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'messages' AND column_name = 'is_from_bot';
        """)
        if not cursor.fetchone():
            cursor.execute("""
                ALTER TABLE messages
                ADD COLUMN is_from_bot BOOLEAN DEFAULT FALSE;
            """)
            conn.commit()
            logger.info("Successfully added 'is_from_bot' column to 'messages' table.")
        else:
            logger.info("Column 'is_from_bot' already exists in 'messages' table.")

    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Error migrating database: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate_database()
