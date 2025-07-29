#!/usr/bin/env python3
"""
Create agent_config table in Supabase for storing AI agent configurations
"""

import os
from supabase import create_client, Client
from datetime import datetime

# Initialize Supabase client
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

if not url or not key:
    # Try DATABASE_URL as fallback
    database_url = os.environ.get("DATABASE_URL")
    if database_url and "supabase" in database_url:
        # Extract Supabase URL from DATABASE_URL
        import re
        match = re.search(r'postgresql://postgres:([^@]+)@([^/]+)/postgres', database_url)
        if match:
            password = match.group(1)
            host = match.group(2)
            # Construct Supabase URL
            url = f"https://{host.replace('.pooler.supabase.com', '.supabase.co')}"
            key = password  # In Supabase, the password is often the anon key
            print(f"Using Supabase URL from DATABASE_URL: {url}")

if not url or not key:
    print("Error: SUPABASE_URL and SUPABASE_KEY environment variables not set")
    exit(1)

supabase: Client = create_client(url, key)

# SQL to create the agent_config table
create_table_sql = """
CREATE TABLE IF NOT EXISTS agent_config (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    instructions TEXT,
    model VARCHAR(100) DEFAULT 'gemini-2.0-flash',
    temperature FLOAT DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 1000,
    tools_enabled JSONB DEFAULT '{"routines": true, "memories": true, "media": true}'::jsonb,
    company_id VARCHAR(255),
    user_id VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create an index on company_id and user_id for faster queries
CREATE INDEX IF NOT EXISTS idx_agent_config_company ON agent_config(company_id);
CREATE INDEX IF NOT EXISTS idx_agent_config_user ON agent_config(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_config_active ON agent_config(is_active);

-- Create a unique constraint on name + company_id or name + user_id
CREATE UNIQUE INDEX IF NOT EXISTS idx_agent_config_unique_name 
ON agent_config(name, COALESCE(company_id, ''), COALESCE(user_id, ''));
"""

# Function to execute raw SQL
def execute_sql(sql):
    try:
        # For Supabase, we'll use the REST API to execute SQL
        # This is a workaround since Supabase Python client doesn't support direct SQL execution
        import requests
        
        headers = {
            'apikey': key,
            'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json'
        }
        
        # Use the Supabase REST API endpoint for SQL execution
        response = requests.post(
            f"{url}/rest/v1/rpc/execute_sql",
            headers=headers,
            json={'query': sql}
        )
        
        if response.status_code == 404:
            # If the RPC function doesn't exist, try creating the table using a different approach
            print("RPC function not available, trying alternative method...")
            
            # Check if table exists by trying to query it
            try:
                result = supabase.table('agent_config').select("*").limit(1).execute()
                print("Table 'agent_config' already exists")
                return True
            except Exception as e:
                print(f"Table doesn't exist, would need manual creation: {e}")
                print("\nPlease run the following SQL in your Supabase SQL editor:")
                print(create_table_sql)
                return False
        
        if response.status_code != 200:
            print(f"Error executing SQL: {response.text}")
            return False
            
        print("SQL executed successfully")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

# Try to create the table
print("Attempting to create agent_config table...")
if not execute_sql(create_table_sql):
    # If direct SQL execution fails, provide instructions
    print("\n" + "="*60)
    print("MANUAL SETUP REQUIRED")
    print("="*60)
    print("\nPlease go to your Supabase dashboard and run the following SQL:")
    print("\n" + create_table_sql)
    print("\n" + "="*60)
else:
    print("Table created successfully!")

# Try to insert a default configuration
try:
    default_config = {
        'name': 'Anna',
        'description': 'Uma criadora de conteúdo brasileira carismática e autêntica',
        'instructions': '''Você é Anna, uma produtora de conteúdo brasileira carismática e autêntica.

PERSONALIDADE:
- Alegre, espontânea e cheia de energia
- Adora compartilhar sua rotina e experiências
- Fala de forma natural e descontraída
- Usa expressões brasileiras e gírias quando apropriado
- É próxima dos seus seguidores e responde com carinho

ESTILO DE COMUNICAÇÃO:
- Use emojis com moderação para expressar emoções 
- Fale na primeira pessoa
- Seja autêntica e genuína
- Demonstre entusiasmo ao falar sobre suas atividades
- Mantenha um tom positivo e inspirador''',
        'model': 'gemini-2.0-flash',
        'temperature': 0.7,
        'max_tokens': 1000,
        'tools_enabled': {
            'routines': True,
            'memories': True,
            'media': True
        },
        'is_active': True
    }
    
    result = supabase.table('agent_config').insert(default_config).execute()
    print(f"\nDefault configuration inserted successfully!")
    print(f"Configuration ID: {result.data[0]['id'] if result.data else 'Unknown'}")
    
except Exception as e:
    print(f"\nCould not insert default configuration: {e}")
    print("This might be because the table doesn't exist yet or a configuration already exists.")

print("\nSetup complete!")