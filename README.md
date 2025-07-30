# Anna Agent - AI-Powered Content Creator Chat

🤖 Uma plataforma de conversação com IA que simula a Anna, uma criadora de conteúdo brasileira carismática e autêntica.

## ✨ Funcionalidades

- **Chat em Tempo Real**: Interface de chat intuitiva e responsiva
- **Personalidade Autêntica**: Anna responde com personalidade brasileira natural
- **Gestão de Rotinas**: Sistema completo de gerenciamento de atividades
- **Múltiplos Canais**: Suporte para WhatsApp, Instagram, Chat Web
- **Banco de Dados Dual**: Sincronização automática PostgreSQL + Supabase
- **Configuração Dinâmica**: Interface para personalizar comportamento da IA

## 🚀 Deploy no Replit

[![Run on Replit](https://replit.com/badge/github/your-username/anna-agent)](https://replit.com/@your-username/anna-agent)

### Configuração Rápida

1. **Fork este repositório**
2. **Configure as variáveis de ambiente:**
   ```
   DATABASE_URL=sua-url-postgresql
   SESSION_SECRET=sua-chave-secreta
   SUPABASE_URL=https://seu-projeto.supabase.co
   SUPABASE_KEY=sua-chave-supabase
   ```
3. **Execute a verificação de saúde:**
   ```bash
   python deployment_health.py
   ```
4. **Inicie a aplicação:**
   ```bash
   gunicorn --bind 0.0.0.0:5000 main:app
   ```

## 🏗️ Arquitetura

### Backend
- **Flask**: Framework web principal
- **Google ADK**: Framework para agentes de IA
- **SQLAlchemy**: ORM para PostgreSQL
- **Supabase**: Banco de dados e storage

### Frontend  
- **HTML5/CSS3/JavaScript**: Interface responsiva
- **Bootstrap 5**: Componentes UI com tema escuro
- **Feather Icons**: Ícones leves

### IA & Machine Learning
- **Google Gemini 2.0 Flash**: Modelo de linguagem
- **Agent Development Kit**: Framework para agentes conversacionais

## 📋 Pré-requisitos

- Python 3.11+
- PostgreSQL 16
- Conta Supabase (opcional)
- Chaves de API do Google

## 🔧 Instalação Local

```bash
# Clone o repositório
git clone https://github.com/your-username/anna-agent.git
cd anna-agent

# Instale dependências
pip install -r requirements.txt

# Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas configurações

# Execute migrações
python setup_database.py

# Inicie a aplicação
python main.py
```

## 🎯 Uso

### Chat Principal
Acesse `/` para conversar com a Anna através da interface web.

### Painel Administrativo  
Acesse `/admin` para:
- Gerenciar atividades e rotinas
- Configurar personalidade da IA
- Visualizar calendário
- Upload de mídia

### API Endpoints
- `GET /health` - Status da aplicação
- `POST /chat` - Envio de mensagens
- `GET /admin/api/activities` - Listar atividades
- `POST /config/api/config` - Salvar configurações

## 🔒 Segurança

- Autenticação via Flask sessions
- Sanitização de dados de entrada
- Verificação de tipos de arquivo
- Headers de segurança configurados

## 📊 Monitoramento

A aplicação inclui:
- Health checks automáticos
- Logs estruturados
- Métricas de performance
- Alertas de erro

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🆘 Suporte

- 📧 Email: support@anna-agent.com
- 💬 Discord: [Anna Agent Community](https://discord.gg/anna-agent)
- 📚 Docs: [Documentação Completa](https://docs.anna-agent.com)

---

Desenvolvido com ❤️ no Brasil 🇧🇷