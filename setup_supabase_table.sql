-- SQL para criar a tabela agent_config no Supabase
-- Execute este SQL no SQL Editor do seu dashboard Supabase

-- Criar a tabela agent_config
CREATE TABLE IF NOT EXISTS agent_config (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(255) NOT NULL DEFAULT 'Anna',
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

-- Criar índices para melhorar performance
CREATE INDEX IF NOT EXISTS idx_agent_config_company ON agent_config(company_id);
CREATE INDEX IF NOT EXISTS idx_agent_config_user ON agent_config(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_config_active ON agent_config(is_active);
CREATE INDEX IF NOT EXISTS idx_agent_config_name ON agent_config(name);

-- Inserir configuração padrão (opcional)
INSERT INTO agent_config (
    name, 
    description, 
    instructions, 
    model, 
    temperature, 
    max_tokens,
    tools_enabled
) VALUES (
    'Anna',
    'AI agent Anna - Criadora de conteúdo brasileira',
    'Você é Anna, uma produtora de conteúdo brasileira carismática e autêntica. SEMPRE use suas ferramentas para consultar dados reais antes de responder.',
    'gemini-2.0-flash',
    0.7,
    1000,
    '{"routines": true, "memories": true, "media": true}'::jsonb
) ON CONFLICT DO NOTHING;

-- Mostrar resultado
SELECT 'Tabela agent_config criada com sucesso!' as resultado;