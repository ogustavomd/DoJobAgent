-- =====================================================
-- SCRIPT COMPLETO PARA CRIAÇÃO DO BANCO ANNA NO SUPABASE
-- =====================================================

-- Habilitar extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- 1. TABELA: routine (Rotinas/Atividades)
-- =====================================================
CREATE TABLE public.routine (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    activity TEXT NOT NULL,
    description TEXT NULL,
    date DATE NOT NULL,
    time_start TIME NULL,
    time_end TIME NULL,
    location TEXT NULL,
    category TEXT NULL DEFAULT 'geral',
    status TEXT NULL DEFAULT 'upcoming',
    has_images BOOLEAN DEFAULT FALSE,
    has_videos BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NULL DEFAULT NOW(),
    CONSTRAINT routine_pkey PRIMARY KEY (id),
    CONSTRAINT routine_status_check CHECK (status = ANY (ARRAY['upcoming'::TEXT, 'current'::TEXT, 'completed'::TEXT])),
    CONSTRAINT routine_category_check CHECK (category = ANY (ARRAY['fitness'::TEXT, 'trabalho'::TEXT, 'social'::TEXT, 'reunião'::TEXT, 'geral'::TEXT]))
);

-- Índices para routine
CREATE INDEX IF NOT EXISTS idx_routine_date ON public.routine USING btree (date);
CREATE INDEX IF NOT EXISTS idx_routine_status ON public.routine USING btree (status);
CREATE INDEX IF NOT EXISTS idx_routine_category ON public.routine USING btree (category);

-- =====================================================
-- 2. TABELA: routine_media (Mídia das Atividades)
-- =====================================================
CREATE TABLE public.routine_media (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    routine_id UUID NOT NULL,
    media_type TEXT NOT NULL DEFAULT 'image',
    media_url TEXT NOT NULL,
    media_caption TEXT NULL,
    created_at TIMESTAMP WITH TIME ZONE NULL DEFAULT NOW(),
    CONSTRAINT routine_media_pkey PRIMARY KEY (id),
    CONSTRAINT routine_media_routine_id_fkey FOREIGN KEY (routine_id) REFERENCES routine (id) ON DELETE CASCADE,
    CONSTRAINT routine_media_type_check CHECK (media_type = ANY (ARRAY['image'::TEXT, 'video'::TEXT]))
);

-- Índices para routine_media
CREATE INDEX IF NOT EXISTS idx_routine_media_routine_id ON public.routine_media USING btree (routine_id);
CREATE INDEX IF NOT EXISTS idx_routine_media_type ON public.routine_media USING btree (media_type);

-- =====================================================
-- 3. TABELA: chat_sessions (Sessões de Chat)
-- =====================================================
CREATE TABLE public.chat_sessions (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    contact_phone TEXT NOT NULL,
    contact_name TEXT NULL,
    contact_avatar TEXT NULL,
    channel TEXT NOT NULL DEFAULT 'chat',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NULL DEFAULT NOW(),
    CONSTRAINT chat_sessions_pkey PRIMARY KEY (id),
    CONSTRAINT chat_sessions_status_check CHECK (status = ANY (ARRAY['active'::TEXT, 'ended'::TEXT])),
    CONSTRAINT chat_sessions_channel_check CHECK (channel = ANY (ARRAY['chat'::TEXT, 'whatsapp'::TEXT, 'instagram'::TEXT, 'web'::TEXT]))
);

-- Índices para chat_sessions
CREATE INDEX IF NOT EXISTS idx_chat_sessions_contact_phone ON public.chat_sessions USING btree (contact_phone);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_channel ON public.chat_sessions USING btree (channel);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_status ON public.chat_sessions USING btree (status);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_updated_at ON public.chat_sessions USING btree (updated_at DESC);

-- =====================================================
-- 4. TABELA: messages (Mensagens dos Chats)
-- =====================================================
CREATE TABLE public.messages (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    chat_session_id UUID NULL,
    sender_phone TEXT NOT NULL,
    sender_name TEXT NULL,
    content TEXT NOT NULL,
    message_type TEXT NULL DEFAULT 'text',
    media_url TEXT NULL,
    is_from_bot BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NULL DEFAULT NOW(),
    CONSTRAINT messages_pkey PRIMARY KEY (id),
    CONSTRAINT messages_chat_session_id_fkey FOREIGN KEY (chat_session_id) REFERENCES chat_sessions (id) ON DELETE CASCADE,
    CONSTRAINT messages_message_type_check CHECK (
        message_type = ANY (ARRAY['text'::TEXT, 'image'::TEXT, 'video'::TEXT, 'audio'::TEXT, 'document'::TEXT])
    )
);

-- Índices para messages
CREATE INDEX IF NOT EXISTS idx_messages_chat_session_id ON public.messages USING btree (chat_session_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON public.messages USING btree (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_sender_phone ON public.messages USING btree (sender_phone);

-- =====================================================
-- 5. TABELA: agents (Configurações dos Agentes)
-- =====================================================
CREATE TABLE public.agents (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    nome TEXT NOT NULL,
    descricao TEXT NULL,
    instrucoes TEXT NOT NULL,
    modelo TEXT NOT NULL DEFAULT 'gemini-2.0-flash',
    temperatura DECIMAL(3,2) DEFAULT 0.70,
    max_tokens INTEGER DEFAULT 1000,
    tools_ativas JSONB NULL DEFAULT '{"routines": true, "memories": true, "media": true}'::JSONB,
    ativo BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMP WITH TIME ZONE NULL DEFAULT NOW(),
    atualizado_em TIMESTAMP WITH TIME ZONE NULL DEFAULT NOW(),
    CONSTRAINT agents_pkey PRIMARY KEY (id),
    CONSTRAINT agents_nome_unique UNIQUE (nome),
    CONSTRAINT agents_temperatura_check CHECK (temperatura >= 0.0 AND temperatura <= 2.0),
    CONSTRAINT agents_max_tokens_check CHECK (max_tokens > 0 AND max_tokens <= 8192)
);

-- Índices para agents
CREATE INDEX IF NOT EXISTS idx_agents_nome ON public.agents USING btree (nome);
CREATE INDEX IF NOT EXISTS idx_agents_ativo ON public.agents USING btree (ativo);

-- =====================================================
-- 6. TABELA: agent_config (Configurações Alternativas)
-- =====================================================
CREATE TABLE public.agent_config (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT NULL,
    instructions TEXT NOT NULL,
    model TEXT NOT NULL DEFAULT 'gemini-2.0-flash',
    temperature DECIMAL(3,2) DEFAULT 0.70,
    max_tokens INTEGER DEFAULT 1000,
    tools_enabled JSONB NULL DEFAULT '{"routines": true, "memories": true, "media": true}'::JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    company_id TEXT NULL,
    user_id TEXT NULL,
    created_at TIMESTAMP WITH TIME ZONE NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NULL DEFAULT NOW(),
    CONSTRAINT agent_config_pkey PRIMARY KEY (id),
    CONSTRAINT agent_config_temperature_check CHECK (temperature >= 0.0 AND temperature <= 2.0),
    CONSTRAINT agent_config_max_tokens_check CHECK (max_tokens > 0 AND max_tokens <= 8192)
);

-- Índices para agent_config
CREATE INDEX IF NOT EXISTS idx_agent_config_name ON public.agent_config USING btree (name);
CREATE INDEX IF NOT EXISTS idx_agent_config_is_active ON public.agent_config USING btree (is_active);
CREATE INDEX IF NOT EXISTS idx_agent_config_company_id ON public.agent_config USING btree (company_id);

-- =====================================================
-- 7. TABELA: clients (Gerenciamento de Clientes)
-- =====================================================
CREATE TABLE public.clients (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    nome TEXT NOT NULL,
    telefone TEXT NOT NULL,
    email TEXT NULL,
    canal_preferido TEXT NOT NULL DEFAULT 'whatsapp',
    avatar_url TEXT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    notas TEXT NULL,
    tags TEXT[] NULL,
    ultima_conversa TIMESTAMP WITH TIME ZONE NULL,
    total_mensagens INTEGER DEFAULT 0,
    data_cadastro TIMESTAMP WITH TIME ZONE NULL DEFAULT NOW(),
    atualizado_em TIMESTAMP WITH TIME ZONE NULL DEFAULT NOW(),
    CONSTRAINT clients_pkey PRIMARY KEY (id),
    CONSTRAINT clients_telefone_unique UNIQUE (telefone),
    CONSTRAINT clients_canal_check CHECK (canal_preferido = ANY (ARRAY['whatsapp'::TEXT, 'instagram'::TEXT, 'chat'::TEXT, 'web'::TEXT]))
);

-- Índices para clients
CREATE INDEX IF NOT EXISTS idx_clients_telefone ON public.clients USING btree (telefone);
CREATE INDEX IF NOT EXISTS idx_clients_ativo ON public.clients USING btree (ativo);
CREATE INDEX IF NOT EXISTS idx_clients_canal_preferido ON public.clients USING btree (canal_preferido);
CREATE INDEX IF NOT EXISTS idx_clients_ultima_conversa ON public.clients USING btree (ultima_conversa DESC);

-- =====================================================
-- 8. TABELA: users (Usuários do Sistema)
-- =====================================================
CREATE TABLE public.users (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    nome TEXT NOT NULL,
    email TEXT NOT NULL,
    telefone TEXT NULL,
    plano TEXT NOT NULL DEFAULT 'gratuito',
    ativo BOOLEAN DEFAULT TRUE,
    permissoes TEXT[] NULL DEFAULT ARRAY['chat'::TEXT],
    configuracoes JSONB NULL DEFAULT '{}'::JSONB,
    ultimo_acesso TIMESTAMP WITH TIME ZONE NULL,
    data_cadastro TIMESTAMP WITH TIME ZONE NULL DEFAULT NOW(),
    atualizado_em TIMESTAMP WITH TIME ZONE NULL DEFAULT NOW(),
    CONSTRAINT users_pkey PRIMARY KEY (id),
    CONSTRAINT users_email_unique UNIQUE (email),
    CONSTRAINT users_plano_check CHECK (plano = ANY (ARRAY['gratuito'::TEXT, 'basico'::TEXT, 'premium'::TEXT, 'enterprise'::TEXT]))
);

-- Índices para users
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users USING btree (email);
CREATE INDEX IF NOT EXISTS idx_users_ativo ON public.users USING btree (ativo);
CREATE INDEX IF NOT EXISTS idx_users_plano ON public.users USING btree (plano);

-- =====================================================
-- 9. TABELA: memories (Memórias)
-- =====================================================
CREATE TABLE public.memories (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    category TEXT NULL DEFAULT 'geral',
    tags TEXT[] NULL,
    importance_level INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    date_referenced DATE NULL,
    created_at TIMESTAMP WITH TIME ZONE NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NULL DEFAULT NOW(),
    CONSTRAINT memories_pkey PRIMARY KEY (id),
    CONSTRAINT memories_importance_check CHECK (importance_level >= 1 AND importance_level <= 5)
);

-- Índices para memories
CREATE INDEX IF NOT EXISTS idx_memories_category ON public.memories USING btree (category);
CREATE INDEX IF NOT EXISTS idx_memories_is_active ON public.memories USING btree (is_active);
CREATE INDEX IF NOT EXISTS idx_memories_importance ON public.memories USING btree (importance_level DESC);
CREATE INDEX IF NOT EXISTS idx_memories_date ON public.memories USING btree (date_referenced DESC);

-- =====================================================
-- 10. TABELA: image_bank (Banco de Imagens)
-- =====================================================
CREATE TABLE public.image_bank (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT NULL,
    image_url TEXT NOT NULL,
    category TEXT NULL DEFAULT 'geral',
    tags TEXT[] NULL,
    is_active BOOLEAN DEFAULT TRUE,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NULL DEFAULT NOW(),
    CONSTRAINT image_bank_pkey PRIMARY KEY (id)
);

-- Índices para image_bank
CREATE INDEX IF NOT EXISTS idx_image_bank_category ON public.image_bank USING btree (category);
CREATE INDEX IF NOT EXISTS idx_image_bank_is_active ON public.image_bank USING btree (is_active);
CREATE INDEX IF NOT EXISTS idx_image_bank_usage ON public.image_bank USING btree (usage_count DESC);

-- =====================================================
-- DADOS DE EXEMPLO PARA DEMONSTRAÇÃO
-- =====================================================

-- Inserir rotinas de exemplo
INSERT INTO public.routine (activity, description, date, time_start, time_end, location, category, status, has_images, has_videos) VALUES
('Treino na academia', 'Treino de força e cardio', CURRENT_DATE, '07:00', '08:30', 'Smart Fit - Vila Madalena', 'fitness', 'upcoming', true, false),
('Gravação de conteúdo', 'Gravação de vídeos para Instagram', CURRENT_DATE, '10:00', '12:00', 'Estúdio em casa', 'trabalho', 'upcoming', true, true),
('Reunião com marca', 'Apresentação de proposta para parceria', CURRENT_DATE, '14:00', '15:30', 'Online - Zoom', 'reunião', 'upcoming', false, false),
('Jantar com amigas', 'Encontro no restaurante japonês', CURRENT_DATE, '19:00', '22:00', 'Restaurante Yamashiro', 'social', 'upcoming', true, false);

-- Inserir agente Anna
INSERT INTO public.agents (nome, descricao, instrucoes, modelo, temperatura, max_tokens, tools_ativas, ativo) VALUES
('Anna', 'Criadora de conteúdo brasileira carismática', 
'Você é Anna, uma criadora de conteúdo brasileira carismática e autêntica. SEMPRE use suas ferramentas para buscar informações reais sobre rotinas, memórias e conteúdo antes de responder.

PERSONALIDADE:
- Carismática, espontânea e autêntica
- Fala em português brasileiro informal
- Usa emojis naturalmente nas conversas
- É fitness, empreendedora e criativa
- Gosta de compartilhar sua rotina e experiências

SEMPRE:
1. Use get_anna_routines() para falar sobre suas atividades
2. Use get_anna_routine_media() para mencionar fotos/vídeos
3. Use search_memories() para relembrar conversas anteriores
4. Use get_recent_conversations() para contexto
5. Seja natural e espontânea nas respostas
6. Fale como uma pessoa real, não como bot', 
'gemini-2.0-flash', 0.7, 1000, 
'{"routines": true, "memories": true, "media": true}'::jsonb, true);

-- Inserir sessões de chat de exemplo
INSERT INTO public.chat_sessions (contact_phone, contact_name, channel, status) VALUES
('+5511999887766', 'João Silva', 'whatsapp', 'active'),
('+5511988776655', 'Maria Santos', 'chat', 'active'),
('web_user', 'Usuário Web', 'chat', 'active');

-- Inserir mensagens de exemplo
WITH session_data AS (
    SELECT id, contact_phone, contact_name FROM chat_sessions
)
INSERT INTO public.messages (chat_session_id, sender_phone, sender_name, content, message_type, is_from_bot) 
SELECT 
    sd.id,
    sd.contact_phone,
    sd.contact_name,
    CASE 
        WHEN sd.contact_name = 'João Silva' THEN 'Oi Anna! Como você está?'
        WHEN sd.contact_name = 'Maria Santos' THEN 'Anna, preciso de umas dicas de treino'
        ELSE 'Olá Anna!'
    END as content,
    'text', 
    false
FROM session_data sd;

-- Inserir respostas da Anna
WITH session_data AS (
    SELECT id, contact_phone, contact_name FROM chat_sessions
)
INSERT INTO public.messages (chat_session_id, sender_phone, sender_name, content, message_type, is_from_bot) 
SELECT 
    sd.id,
    'anna_bot',
    'Anna',
    CASE 
        WHEN sd.contact_name = 'João Silva' THEN 'Oi João! Estou ótima, obrigada! 😊 Como foi seu dia?'
        WHEN sd.contact_name = 'Maria Santos' THEN 'Claro, Maria! Adoro falar sobre fitness! 💪 Que tipo de treino você tem interesse?'
        ELSE 'Olá! Tudo bem? Como posso te ajudar hoje? 😊'
    END as content,
    'text', 
    true
FROM session_data sd;

-- Inserir clientes de exemplo
INSERT INTO public.clients (nome, telefone, email, canal_preferido, ativo, notas, ultima_conversa, total_mensagens) VALUES
('João Silva', '+5511999887766', 'joao@email.com', 'whatsapp', true, 'Cliente interessado em fitness', NOW() - INTERVAL '1 hour', 5),
('Maria Santos', '+5511988776655', 'maria@email.com', 'chat', true, 'Busca dicas de treino', NOW() - INTERVAL '2 hours', 3),
('Carlos Oliveira', '+5511977665544', 'carlos@email.com', 'instagram', true, 'Seguidor do Instagram', NOW() - INTERVAL '1 day', 2);

-- Inserir usuários de exemplo
INSERT INTO public.users (nome, email, telefone, plano, ativo, permissoes, ultimo_acesso) VALUES
('Admin Sistema', 'admin@anna.com', '+5511999999999', 'enterprise', true, ARRAY['chat', 'admin', 'config'], NOW()),
('Usuário Teste', 'teste@anna.com', '+5511888888888', 'premium', true, ARRAY['chat', 'view'], NOW() - INTERVAL '1 day');

-- Inserir memórias de exemplo
INSERT INTO public.memories (title, content, category, tags, importance_level, is_active, date_referenced) VALUES
('Primeiro treino na academia', 'Lembro que estava nervosa no meu primeiro dia na academia, mas acabou sendo incrível!', 'fitness', ARRAY['treino', 'academia', 'começo'], 4, true, CURRENT_DATE - INTERVAL '30 days'),
('Parceria com marca de suplementos', 'Fechei minha primeira parceria grande com uma marca conhecida de whey protein', 'trabalho', ARRAY['parceria', 'marca', 'suplementos'], 5, true, CURRENT_DATE - INTERVAL '15 days'),
('Receita de smoothie verde', 'Criei uma receita deliciosa de smoothie verde que virou hit no Instagram', 'receitas', ARRAY['smoothie', 'saudável', 'receita'], 3, true, CURRENT_DATE - INTERVAL '7 days');

-- Inserir banco de imagens de exemplo
INSERT INTO public.image_bank (title, description, image_url, category, tags, is_active, usage_count) VALUES
('Treino na academia', 'Foto fazendo agachamento na academia', 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b', 'fitness', ARRAY['treino', 'academia', 'agachamento'], true, 5),
('Smoothie verde', 'Foto do smoothie verde com ingredientes', 'https://images.unsplash.com/photo-1610970881699-44a5587cabec', 'alimentação', ARRAY['smoothie', 'saudável', 'verde'], true, 8),
('Estúdio de gravação', 'Setup de gravação em casa com ring light', 'https://images.unsplash.com/photo-1611532736597-de2d4265fba3', 'trabalho', ARRAY['gravação', 'estúdio', 'conteúdo'], true, 12),
('Look do dia', 'Outfit casual para o dia a dia', 'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f', 'moda', ARRAY['outfit', 'look', 'casual'], true, 3);

-- =====================================================
-- FINALIZAÇÃO DO SCRIPT
-- =====================================================

-- Atualizar sequences e contadores se necessário
SELECT setval(pg_get_serial_sequence('routine', 'id'), COALESCE(MAX(id::text::int), 1)) FROM routine WHERE id::text ~ '^[0-9]+$';

-- Verificar se tudo foi criado corretamente
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Mostrar contagem de registros por tabela
SELECT 
    'routine' as tabela, COUNT(*) as registros FROM routine
UNION ALL
SELECT 'routine_media', COUNT(*) FROM routine_media
UNION ALL
SELECT 'chat_sessions', COUNT(*) FROM chat_sessions
UNION ALL
SELECT 'messages', COUNT(*) FROM messages
UNION ALL
SELECT 'agents', COUNT(*) FROM agents
UNION ALL
SELECT 'clients', COUNT(*) FROM clients
UNION ALL
SELECT 'users', COUNT(*) FROM users
UNION ALL
SELECT 'memories', COUNT(*) FROM memories
UNION ALL
SELECT 'image_bank', COUNT(*) FROM image_bank
ORDER BY tabela;

-- =====================================================
-- INSTRUÇÕES DE USO:
-- 
-- 1. Copie todo este script
-- 2. Acesse o Supabase Dashboard > SQL Editor
-- 3. Cole e execute o script completo
-- 4. Verifique os resultados das consultas finais
-- 5. Configure as variáveis de ambiente:
--    - SUPABASE_URL: sua URL do projeto
--    - SUPABASE_KEY: sua chave anon/service_role
-- 
-- O script cria todas as tabelas necessárias com:
-- - Estrutura completa com UUIDs
-- - Índices otimizados para performance
-- - Constraints de integridade
-- - Dados de exemplo para teste
-- =====================================================