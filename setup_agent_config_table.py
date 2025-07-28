#!/usr/bin/env python3
"""
Script to create the agent_configurations table in Supabase
"""

import logging
from supabase_tools import supabase

def setup_agent_config_table():
    """Create the agent_configurations table if it doesn't exist"""
    try:
        # SQL to create the table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS agent_configurations (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL DEFAULT 'Anna',
            model VARCHAR(100) NOT NULL DEFAULT 'gemini-2.0-flash',
            description TEXT,
            instructions TEXT NOT NULL,
            tools TEXT NOT NULL, -- JSON array of tool names
            temperature DECIMAL(3,2) DEFAULT 0.7,
            max_tokens INTEGER DEFAULT 1000,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        # Execute the SQL using Supabase RPC (if available) or alternative method
        print("Creating agent_configurations table...")
        
        # Try to create table using supabase.rpc if available, otherwise inform user
        try:
            # This might not work if RPC is not set up, but worth trying
            result = supabase.rpc('exec_sql', {'sql': create_table_sql}).execute()
            print(f"Table created successfully: {result}")
        except Exception as rpc_error:
            print(f"RPC method failed: {rpc_error}")
            print("Please create the following table manually in your Supabase dashboard:")
            print(create_table_sql)
            
            # Alternative: Try to insert a test record to see if table exists
            try:
                test_config = {
                    'name': 'Anna',
                    'model': 'gemini-2.0-flash',
                    'description': 'Test config',
                    'instructions': 'Test instructions',
                    'tools': '["get_anna_routines"]',
                    'temperature': 0.7,
                    'max_tokens': 1000,
                    'is_active': False
                }
                
                # Try to insert - this will fail if table doesn't exist
                result = supabase.table('agent_configurations').insert(test_config).execute()
                print("Table already exists or was created successfully!")
                
                # Clean up test record
                if result.data:
                    supabase.table('agent_configurations').delete().eq('id', result.data[0]['id']).execute()
                    print("Test record cleaned up")
                    
            except Exception as insert_error:
                print(f"Table does not exist. Error: {insert_error}")
                print("\nPlease create the table manually in Supabase SQL Editor:")
                print(create_table_sql)
                
    except Exception as e:
        logging.error(f"Error setting up agent_configurations table: {e}")
        print(f"Error: {e}")
        print("\nPlease create the table manually in Supabase SQL Editor:")
        print(create_table_sql)

if __name__ == "__main__":
    setup_agent_config_table()