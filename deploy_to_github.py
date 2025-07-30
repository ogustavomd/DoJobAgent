#!/usr/bin/env python3
"""
Deploy to GitHub Script
Automated deployment helper for Anna Agent
"""

import os
import subprocess
import sys

def run_command(command, description=""):
    """Run shell command and handle errors"""
    print(f"🔄 {description}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Error: {result.stderr}")
            return False
        if result.stdout:
            print(f"✅ {result.stdout.strip()}")
        return True
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    print("🚀 ANNA AGENT - DEPLOY TO GITHUB")
    print("=" * 50)
    
    # Get repository URL from user
    repo_url = input("📝 Digite a URL do seu repositório GitHub (ex: https://github.com/username/anna-agent): ")
    if not repo_url:
        print("❌ URL do repositório é obrigatória!")
        sys.exit(1)
    
    print("\n📋 CHECKLIST PRÉ-DEPLOY:")
    
    # Check if git is available
    if not run_command("git --version", "Verificando Git"):
        print("❌ Git não encontrado! Instale o Git primeiro.")
        sys.exit(1)
    
    # Check if we're in a git repository
    if not os.path.exists('.git'):
        print("📦 Inicializando repositório Git...")
        if not run_command("git init", "Inicializando Git"):
            sys.exit(1)
    
    # Add all files
    print("📁 Adicionando arquivos...")
    if not run_command("git add .", "Adicionando todos os arquivos"):
        sys.exit(1)
    
    # Check for changes
    result = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)
    if not result.stdout.strip():
        print("ℹ️  Nenhuma mudança detectada para commit")
    else:
        # Commit changes
        commit_message = "Deploy inicial do Anna Agent com correções de banco"
        if not run_command(f'git commit -m "{commit_message}"', "Fazendo commit"):
            sys.exit(1)
    
    # Set main branch
    if not run_command("git branch -M main", "Configurando branch main"):
        sys.exit(1)
    
    # Add remote origin
    if not run_command(f"git remote add origin {repo_url}", "Adicionando remote origin"):
        # If remote already exists, update it
        run_command(f"git remote set-url origin {repo_url}", "Atualizando remote origin")
    
    # Push to GitHub
    print("🚀 Fazendo push para GitHub...")
    if not run_command("git push -u origin main", "Enviando código para GitHub"):
        print("⚠️  Se der erro de autenticação, você pode:")
        print("   1. Configurar SSH keys no GitHub")
        print("   2. Usar GitHub CLI: gh auth login")
        print("   3. Fazer push manual via interface do Replit")
        sys.exit(1)
    
    print("\n✅ DEPLOY CONCLUÍDO COM SUCESSO!")
    print("=" * 50)
    print("🔗 Próximos passos:")
    print("1. Acesse seu repositório no GitHub")
    print("2. Vá para Replit.com e crie um novo Repl")
    print("3. Selecione 'Import from GitHub'")
    print("4. Cole a URL do seu repositório")
    print("5. Configure as variáveis de ambiente (DATABASE_URL, SESSION_SECRET)")
    print("6. Clique em 'Run' para iniciar!")
    print("\n📖 Para instruções detalhadas, veja: DEPLOY_REPLIT.md")

if __name__ == "__main__":
    main()