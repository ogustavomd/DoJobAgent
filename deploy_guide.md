# Guia de Deploy - Anna Agent

## 🚀 Deploy Automático no Replit

### 1. Preparação do Repositório GitHub

1. **Crie um novo repositório no GitHub:**
   ```bash
   # No seu GitHub, clique em "New repository"
   # Nome: anna-agent-chat
   # Descrição: AI-Powered Content Creator Chat Bot
   # Público ou Privado (sua escolha)
   ```

2. **Configure o repositório local:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Anna Agent with database fixes"
   git branch -M main
   git remote add origin https://github.com/SEU-USERNAME/anna-agent-chat.git
   git push -u origin main
   ```

### 2. Deploy no Replit

1. **Acesse [Replit.com](https://replit.com)**
2. **Clique em "Create Repl"**
3. **Selecione "Import from GitHub"**
4. **Cole a URL do seu repositório**
5. **Configure as variáveis de ambiente:**

   No Replit, vá em Secrets e adicione:
   ```
   DATABASE_URL=postgresql://username:password@host/database
   SESSION_SECRET=sua-chave-secreta-super-forte
   SUPABASE_URL=https://seu-projeto.supabase.co
   SUPABASE_KEY=sua-chave-publica-supabase
   ```

6. **Clique em "Run" para iniciar**

### 3. Configuração de Banco de Dados

#### Opção A: Replit Database (Simples)
```bash
# O Replit criará automaticamente um PostgreSQL
# A variável DATABASE_URL será configurada automaticamente
```

#### Opção B: Supabase (Recomendado)
1. Crie conta em [supabase.com](https://supabase.com)
2. Crie novo projeto
3. Vá em Settings > API
4. Copie URL e anon key para as variáveis de ambiente

#### Opção C: Neon.tech (Gratuito)
1. Crie conta em [neon.tech](https://neon.tech)
2. Crie novo projeto
3. Copie connection string para DATABASE_URL

### 4. Verificação do Deploy

Execute a verificação de saúde:
```bash
python deployment_health.py
```

Deve retornar:
```
✅ Deployment is healthy and ready!
```

### 5. Acesso à Aplicação

- **Chat Principal:** `https://seu-repl.replit.app/`
- **Admin Panel:** `https://seu-repl.replit.app/admin`
- **Health Check:** `https://seu-repl.replit.app/health`

## 🔧 Deploy Manual (Docker)

### 1. Usando Docker Compose

```bash
# Clone o repositório
git clone https://github.com/SEU-USERNAME/anna-agent-chat.git
cd anna-agent-chat

# Configure .env
cp .env.example .env
# Edite .env com suas configurações

# Inicie com Docker
docker-compose up -d

# Verifique logs
docker-compose logs -f anna-agent
```

### 2. Deploy em VPS/Cloud

```bash
# Conecte ao seu servidor
ssh user@seu-servidor.com

# Clone e configure
git clone https://github.com/SEU-USERNAME/anna-agent-chat.git
cd anna-agent-chat
pip install -r requirements.txt

# Configure nginx (opcional)
sudo nano /etc/nginx/sites-available/anna-agent

# Inicie com systemd
sudo systemctl enable anna-agent
sudo systemctl start anna-agent
```

## 🏗️ Deploy em Plataformas Cloud

### Railway
1. Conecte GitHub ao Railway
2. Selecione o repositório
3. Configure variáveis de ambiente
4. Deploy automático

### Heroku
```bash
heroku create anna-agent-chat
heroku addons:create heroku-postgresql:hobby-dev
git push heroku main
```

### Vercel (Frontend Only)
```bash
npm install -g vercel
vercel --prod
```

## 🔍 Troubleshooting

### Erro de Conexão com Banco
```bash
# Verifique variáveis de ambiente
echo $DATABASE_URL

# Teste conexão
python -c "import psycopg2; print('OK')"

# Execute verificação
python deployment_health.py
```

### Erro de Dependências
```bash
# Reinstale dependências
pip install --upgrade -r requirements.txt

# Limpe cache
pip cache purge
```

### Erro de Permissões
```bash
# Corrija permissões
chmod +x *.py
chown -R app:app /app
```

## 📋 Checklist Pós-Deploy

- [ ] Health check retorna status "healthy"
- [ ] Chat interface carrega corretamente
- [ ] Admin panel acessível
- [ ] Banco de dados conectado
- [ ] Logs sem erros críticos
- [ ] HTTPS configurado (produção)
- [ ] Backup configurado
- [ ] Monitoramento ativo

## 🆘 Suporte

Se encontrar problemas:

1. **Verifique logs:** `docker-compose logs anna-agent`
2. **Execute health check:** `python deployment_health.py`
3. **Consulte documentação:** [replit.md](./replit.md)
4. **Contato:** Abra uma issue no GitHub

---

✅ **Deploy concluído com sucesso!** Sua Anna Agent está pronta para conversar! 🤖💬