#!/usr/bin/env python3
"""Create agent_config table using Supabase REST API"""

import os
import requests
import json

# Get Supabase credentials
url = os.environ.get("SUPABASE_URL", "")
key = os.environ.get("SUPABASE_KEY", "")

# Extract from DATABASE_URL if not set
if not url or not key:
    database_url = os.environ.get("DATABASE_URL", "")
    if database_url and "supabase" in database_url:
        import re
        match = re.search(r'postgresql://postgres\.([^:]+):([^@]+)@([^/]+)/postgres', database_url)
        if match:
            project_ref = match.group(1)
            password = match.group(2)
            host = match.group(3)
            # Construct Supabase URL
            url = f"https://{project_ref}.supabase.co"
            key = password  # In Supabase, the password is often the service_role key
            print(f"Using Supabase URL: {url}")

if not url or not key:
    print("Error: Could not determine Supabase URL and key")
    exit(1)

# Headers for Supabase REST API
headers = {
    'apikey': key,
    'Authorization': f'Bearer {key}',
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

print(f"Supabase project: {url}")

# First, let's check if we can connect
test_response = requests.get(f"{url}/rest/v1/", headers=headers)
print(f"Connection test status: {test_response.status_code}")

# SQL to create the table via RPC function (if available)
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

CREATE INDEX IF NOT EXISTS idx_agent_config_company ON agent_config(company_id);
CREATE INDEX IF NOT EXISTS idx_agent_config_user ON agent_config(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_config_active ON agent_config(is_active);
"""

print("\n" + "="*60)
print("MANUAL SETUP REQUIRED")
print("="*60)
print("\nPlease create the agent_config table in your Supabase dashboard:")
print(f"\n1. Go to: {url}")
print("2. Navigate to the SQL Editor")
print("3. Run the following SQL:\n")
print(create_table_sql)
print("\n" + "="*60)
print("\nAfter creating the table, the configuration saving feature will work.")
