#!/usr/bin/env python3
"""Simple test to check Supabase connection and table"""

from supabase_tools import supabase

try:
    # Try to query the agent_config table
    result = supabase.table('agent_config').select("*").limit(1).execute()
    print(f"✅ Table exists! Found {len(result.data)} records")
    
    if result.data:
        print(f"\nFirst record columns: {list(result.data[0].keys())}")
    else:
        print("\nNo records found in table")
        
except Exception as e:
    print(f"❌ Error accessing agent_config table: {e}")
    print("\nThis might mean the table doesn't exist yet")
