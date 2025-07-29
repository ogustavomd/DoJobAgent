#!/usr/bin/env python3
"""
Setup script for agent_config table in Supabase

This script provides the SQL needed to create the agent_config table in your Supabase project.
"""

print("""
========================================================================
SUPABASE AGENT CONFIGURATION TABLE SETUP
========================================================================

To enable agent configuration saving/loading, you need to create a table
in your Supabase project. Please follow these steps:

1. Go to your Supabase Dashboard
2. Navigate to the SQL Editor
3. Run the following SQL:

------------------------------------------------------------------------

-- Create the agent_config table
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

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_agent_config_company ON agent_config(company_id);
CREATE INDEX IF NOT EXISTS idx_agent_config_user ON agent_config(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_config_active ON agent_config(is_active);

-- Create a unique constraint on name + company_id + user_id
CREATE UNIQUE INDEX IF NOT EXISTS idx_agent_config_unique_name 
ON agent_config(name, COALESCE(company_id, ''), COALESCE(user_id, ''));

-- Insert a default Anna configuration
INSERT INTO agent_config (
    name,
    description,
    instructions,
    model,
    temperature,
    max_tokens,
    tools_enabled,
    is_active
) VALUES (
    'Anna',
    'Uma criadora de conteúdo brasileira carismática e autêntica',
    'Você é Anna, uma produtora de conteúdo brasileira carismática e autêntica.

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
- Mantenha um tom positivo e inspirador

IMPORTANTE: Sempre consulte o banco de dados antes de responder.',
    'gemini-2.0-flash',
    0.8,
    1000,
    '{"routines": true, "memories": true, "media": true}'::jsonb,
    true
);

------------------------------------------------------------------------

4. After running the SQL, the agent configuration features will be available!

========================================================================
FEATURES ENABLED AFTER SETUP:
========================================================================

✅ Save and load agent configurations by company/user
✅ Edit agent personality and instructions
✅ Configure model settings (temperature, max tokens)
✅ Enable/disable specific tools (routines, memories, media)
✅ Multiple configurations for different companies/users

========================================================================
""")