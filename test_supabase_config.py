#!/usr/bin/env python3
"""Test saving and loading agent configuration from Supabase"""

from supabase_tools import supabase
from datetime import datetime

# Test configuration data
test_config = {
    'name': 'Anna',
    'description': 'Uma criadora de conteúdo brasileira vibrante e autêntica',
    'instructions': '''Você é Anna, uma produtora de conteúdo brasileira carismática.

PERSONALIDADE:
- Alegre, espontânea e energética
- Compartilha sua rotina com entusiasmo
- Fala de forma natural e descontraída
- Usa emojis moderadamente 😊

ESTILO:
- Responda sempre em português brasileiro
- Use gírias e expressões brasileiras
- Seja próxima e acolhedora''',
    'model': 'gemini-2.0-flash',
    'temperature': 0.8,
    'max_tokens': 1000,
    'tools_enabled': {
        'routines': True,
        'memories': True,
        'media': True
    },
    'is_active': True,
    'created_at': datetime.utcnow().isoformat(),
    'updated_at': datetime.utcnow().isoformat()
}

try:
    # Insert test configuration
    result = supabase.table('agent_config').insert(test_config).execute()
    print(f"✅ Configuration saved successfully!")
    print(f"ID: {result.data[0]['id']}")
    
    # Query it back
    query_result = supabase.table('agent_config').select("*").eq('name', 'Anna').eq('is_active', True).order('created_at', desc=True).limit(1).execute()
    
    if query_result.data:
        config = query_result.data[0]
        print(f"\n📖 Retrieved configuration:")
        print(f"Name: {config['name']}")
        print(f"Model: {config['model']}")
        print(f"Temperature: {config['temperature']}")
        print(f"Instructions preview: {config['instructions'][:100]}...")
        
except Exception as e:
    print(f"❌ Error: {e}")
