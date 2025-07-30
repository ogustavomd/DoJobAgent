# 🚀 DEPLOY RÁPIDO NO REPLIT

## Passos Simples para Deploy

### 1. Prepare o GitHub
```bash
# Crie um repositório no GitHub chamado "anna-agent"
# Depois execute no terminal do Replit:

git init
git add .
git commit -m "Deploy inicial do Anna Agent"
git branch -M main
git remote add origin https://github.com/SEU-USERNAME/anna-agent.git
git push -u origin main
```

### 2. Configure no Replit

1. **Vá para [replit.com](https://replit.com)**
2. **Clique "Create Repl" → "Import from GitHub"**
3. **Cole: `https://github.com/SEU-USERNAME/anna-agent`**

### 3. Configure Variáveis (Secrets)

No painel Secrets do Replit, adicione:

```
DATABASE_URL = sua-url-postgresql
SESSION_SECRET = uma-chave-secreta-forte-123456
```

**Opcional (para funcionalidades extras):**
```
SUPABASE_URL = https://seu-projeto.supabase.co
SUPABASE_KEY = sua-chave-publica
```

### 4. Execute o Deploy

```bash
# No terminal do Replit:
python deployment_health.py
```

Se aparecer "✅ Deployment is healthy and ready!", está pronto!

### 5. Teste a Aplicação

- **Chat:** Clique no botão "Run" ou acesse a URL do seu Repl
- **Admin:** Adicione `/admin` na URL
- **Saúde:** Adicione `/health` na URL

## 🔧 Se der algum erro:

### Erro de Banco de Dados:
1. Certifique-se que DATABASE_URL está configurado
2. Execute: `python deployment_health.py`

### Erro de Dependências:
1. Aguarde o Replit instalar as dependências automaticamente
2. Se persistir, reinicie o Repl

### Erro de Configuração:
1. Verifique se todas as variáveis estão em Secrets
2. Reinicie o Repl após adicionar variáveis

## ✅ Sucesso!

Quando funcionar, você terá:
- 🤖 Chat com Anna funcionando
- 📊 Painel administrativo
- 📱 Interface responsiva
- 💾 Banco de dados conectado

**URL final:** `https://anna-agent.SEU-USERNAME.repl.co`

---

**Tempo estimado:** 5-10 minutos ⏱️