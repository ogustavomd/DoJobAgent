import logging
from app import app, db
from models import Routine, RoutineMedia, ChatSession, Message, Memory, Agent

def create_tables():
    """Create all database tables"""
    try:
        with app.app_context():
            print("Dropping all database tables...")
            db.drop_all()
            print("Creating all database tables...")
            db.create_all()
            print("✓ All tables created successfully")
            return True
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        return False

def main():
    """Main setup function"""
    print("Setting up PostgreSQL database...")
    
    success = create_tables()
    
    if success:
        print("\n✓ PostgreSQL database setup completed successfully!")
        with app.app_context():
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print("\nTables in database:")
            for table in tables:
                print(f"- {table}")
            
            print("\nColumns in chat_sessions table:")
            columns = inspector.get_columns('chat_sessions')
            for column in columns:
                print(f"- {column['name']}")
    else:
        print("\n✗ PostgreSQL database setup failed")
    
    return success

if __name__ == "__main__":
    main()
