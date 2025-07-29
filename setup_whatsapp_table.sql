-- SQL para criar tabela de conversas WhatsApp no Supabase
-- Execute este SQL no SQL Editor do seu dashboard Supabase

-- Criar a tabela whatsapp_conversations
CREATE TABLE IF NOT EXISTS whatsapp_conversations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    user_message TEXT NOT NULL,
    anna_response TEXT NOT NULL,
    platform VARCHAR(20) DEFAULT 'whatsapp',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Criar índices para melhorar performance
CREATE INDEX IF NOT EXISTS idx_whatsapp_phone ON whatsapp_conversations(phone_number);
CREATE INDEX IF NOT EXISTS idx_whatsapp_created ON whatsapp_conversations(created_at);
CREATE INDEX IF NOT EXISTS idx_whatsapp_platform ON whatsapp_conversations(platform);

-- Criar tabela de configuração WhatsApp
CREATE TABLE IF NOT EXISTS whatsapp_config (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    evolution_url VARCHAR(255) NOT NULL,
    instance_name VARCHAR(100) DEFAULT 'anna_bot',
    webhook_url VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Comentários nas tabelas
COMMENT ON TABLE whatsapp_conversations IS 'Armazena conversas entre usuários e Anna via WhatsApp';
COMMENT ON TABLE whatsapp_config IS 'Configurações da integração WhatsApp Evolution API';

-- Mostrar resultado
SELECT 'Tabelas WhatsApp criadas com sucesso!' as resultado;