# 📱 Integração WhatsApp - Anna Agent

Este documento explica como configurar e usar a integração WhatsApp com a Anna através da Evolution API v2.

## 🚀 Configuração Inicial

### 1. Docker Evolution API

Execute o Docker Compose para iniciar a Evolution API:

```bash
# Execute este comando na raiz do projeto
docker-compose -f docker-compose.evolution.yml up -d
```

**Importante:** Modifique as seguintes variáveis no `docker-compose.evolution.yml`:
- `POSTGRES_PASSWORD`: Troque `SuaSenhaSegura123` por uma senha forte
- `AUTHENTICATION_API_KEY`: Troque `mude-me-para-uma-chave-segura` por uma chave segura

### 2. Configuração na Interface

1. Acesse a interface administrativa: `/admin`
2. Clique no botão **📱 WhatsApp** no cabeçalho
3. Preencha os dados:
   - **URL da Evolution API**: `http://localhost:8080` (ou sua URL)
   - **API Key**: A chave configurada no Docker
   - **Nome da Instância**: `anna_bot` (ou personalize)
   - **Webhook URL**: `https://sua-app.com/webhook/whatsapp` (opcional)

### 3. Conectar WhatsApp

1. Clique em **Inicializar Integração**
2. Escaneie o QR Code com seu WhatsApp:
   - Abra WhatsApp > Menu > Dispositivos conectados
   - Clique em "Conectar um dispositivo"
   - Escaneie o QR Code exibido na tela

## 🛠️ Funcionalidades

### ✅ Implementadas

- **Configuração Visual**: Interface completa de configuração
- **Conexão WhatsApp**: QR Code automático e status de conexão
- **Mensagens Automáticas**: Anna responde automaticamente às mensagens
- **Processamento Inteligente**: Usa o mesmo agente AI da interface web
- **Webhook Handler**: Processa mensagens recebidas em tempo real
- **Teste de Mensagens**: Interface para testar envio de mensagens
- **Logs de Conversa**: Salva conversas no banco Supabase

### 📋 Endpoints da API

- `GET /whatsapp/config` - Interface de configuração
- `POST /whatsapp/api/initialize` - Inicializar integração
- `GET /whatsapp/api/status` - Status da conexão
- `GET /whatsapp/api/qr-code` - Obter QR Code
- `POST /whatsapp/api/send-message` - Enviar mensagem
- `POST /webhook/whatsapp` - Webhook para receber mensagens

### 🗄️ Tabelas do Banco

Execute o SQL em `setup_whatsapp_table.sql` no Supabase:

```sql
-- Tabela de conversas WhatsApp
CREATE TABLE whatsapp_conversations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    user_message TEXT NOT NULL,
    anna_response TEXT NOT NULL,
    platform VARCHAR(20) DEFAULT 'whatsapp',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de configuração WhatsApp  
CREATE TABLE whatsapp_config (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    evolution_url VARCHAR(255) NOT NULL,
    instance_name VARCHAR(100) DEFAULT 'anna_bot',
    webhook_url VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## 🔧 Configuração Avançada

### Variáveis de Ambiente

Opcionalmente, configure essas variáveis:

```bash
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=sua-api-key-aqui
EVOLUTION_INSTANCE_NAME=anna_bot
EVOLUTION_WEBHOOK_URL=https://sua-app.com/webhook/whatsapp
```

### Webhook Automático

Para receber mensagens automaticamente:

1. Configure uma URL pública (use ngrok para desenvolvimento)
2. Defina a URL no campo "Webhook URL" 
3. A Anna responderá automaticamente às mensagens recebidas

```bash
# Exemplo com ngrok para desenvolvimento
ngrok http 5000
# Use a URL ngrok como webhook: https://abc123.ngrok.io/webhook/whatsapp
```

## 📱 Como Usar

### Usuário Final

1. Adicione o número conectado nos contatos
2. Envie uma mensagem no WhatsApp
3. Anna responderá automaticamente usando suas rotinas e dados
4. Conversas são salvas no banco para memória futura

### Administrador

1. Monitor conexão na interface `/whatsapp/config`
2. Teste mensagens através da interface
3. Visualize conversas na seção de teste
4. Reconecte se necessário (QR Code atualiza automaticamente)

## 🚨 Solução de Problemas

### Docker não inicia
- Verifique se as portas 8080, 5432 e 6379 estão livres
- Confirme que Docker está rodando
- Verifique logs: `docker-compose -f docker-compose.evolution.yml logs -f`

### QR Code não aparece
- Verifique se a API Key está correta
- Confirme que a Evolution API está respondendo
- Tente reiniciar a instância na interface

### Mensagens não chegam
- Confirme que o webhook está configurado
- Verifique se a URL está pública (não localhost)
- Monitore logs de webhook no console

### Anna não responde
- Verifique se o agente está inicializado
- Confirme conexão com Supabase
- Monitore logs da aplicação

## 📚 Documentação Evolution API

- [Documentação oficial](https://doc.evolution-api.com/v2/pt)
- [Variáveis de ambiente](https://doc.evolution-api.com/v2/pt/env)
- [Webhooks](https://doc.evolution-api.com/v2/pt/integrations/webhook)

## 🔄 Próximas Melhorias

- [ ] Interface para múltiplas instâncias
- [ ] Botões interativos (quick replies)
- [ ] Envio de mídia (imagens/vídeos)
- [ ] Integração com calendário (agendamentos)
- [ ] Relatórios de conversas
- [ ] Notificações push para admin