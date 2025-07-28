#!/usr/bin/env python3
"""
Setup script to create necessary database tables
"""
import logging
from supabase_tools import supabase

def create_agent_configurations_table():
    """Create agent_configurations table if it doesn't exist"""
    try:
        # Check if table exists by trying to select from it
        try:
            supabase.table('agent_configurations').select('id').limit(1).execute()
            print("✓ agent_configurations table already exists")
            return True
        except Exception:
            pass
        
        # Create table using raw SQL
        sql_query = """
        CREATE TABLE IF NOT EXISTS agent_configurations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            model VARCHAR(100) NOT NULL DEFAULT 'gemini-2.0-flash',
            description TEXT,
            instructions TEXT NOT NULL,
            tools_enabled JSONB DEFAULT '[]'::jsonb,
            temperature DECIMAL(3,2) DEFAULT 0.7,
            max_tokens INTEGER DEFAULT 1000,
            is_active BOOLEAN DEFAULT false,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        response = supabase.rpc('exec_sql', {'sql': sql_query}).execute()
        print("✓ agent_configurations table created successfully")
        return True
        
    except Exception as e:
        print(f"✗ Error creating agent_configurations table: {e}")
        return False

def fix_messages_table():
    """Fix messages table schema"""
    try:
        # Check current schema
        result = supabase.table('messages').select('*').limit(1).execute()
        columns = list(result.data[0].keys()) if result.data else []
        print(f"Messages table columns: {columns}")
        
        # Add missing columns if needed
        if 'assistant_response' not in columns:
            sql_query = """
            ALTER TABLE messages 
            ADD COLUMN IF NOT EXISTS assistant_response TEXT;
            """
            supabase.rpc('exec_sql', {'sql': sql_query}).execute()
            print("✓ Added assistant_response column to messages table")
        
        return True
        
    except Exception as e:
        print(f"✗ Error fixing messages table: {e}")
        return False

def main():
    """Main setup function"""
    print("Setting up database tables...")
    
    success = True
    success &= create_agent_configurations_table()
    success &= fix_messages_table()
    
    if success:
        print("\n✓ Database setup completed successfully!")
    else:
        print("\n✗ Some database setup steps failed")
    
    return success

if __name__ == "__main__":
    main()